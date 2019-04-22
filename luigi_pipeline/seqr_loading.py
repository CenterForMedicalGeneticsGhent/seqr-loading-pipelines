import logging

import luigi
import hail as hl

from lib.hail_tasks import HailMatrixTableTask, HailElasticSearchTask, GCSorLocalTarget, MatrixTableSampleSetError
from hail_scripts.v02.utils.computed_fields import variant_id
from hail_scripts.v02.utils.computed_fields import vep
from lib.model.seqr_mt_schema import SeqrVariantSchema

logger = logging.getLogger(__name__)


class SeqrValidationError(Exception):
    pass

class SeqrVCFToMTTask(HailMatrixTableTask):
    """
    Inherits from a Hail MT Class to get helper function logic. Main logic to do annotations here.
    """
    reference_mt_path = luigi.Parameter(description='Path to the matrix table storing the reference variants.')
    sample_type = luigi.ChoiceParameter(choices=['WGS', 'WES'], description='Sample type, WGS or WES', var_type=str)
    validate = luigi.BoolParameter(default=True, description='Perform validation on the dataset.')
    dataset_type = luigi.ChoiceParameter(choices=['VARIANTS', 'SV'], default='VARIANTS', description='VARIANTS or SV.')
    remap_path = luigi.OptionalParameter(default=None, description="Path to a tsv file with two columns: s and seqr_id.")
    subset_path = luigi.OptionalParameter(default=None, description="Path to a tsv file with one column of sample IDs: s.")

    def run(self):
        mt = self.import_vcf()
        if self.validate:
            self.validate_mt(mt, self.genome_version, self.sample_type)
        if self.remap_path:
            mt = self.remap_sample_ids(mt, self.remap_path)
        if self.subset_path:
            mt = self.subset_samples_and_variants(mt, self.subset_path)
        mt = hl.split_multi(mt)
        mt = HailMatrixTableTask.run_vep(mt, self.genome_version, self.vep_runner)

        Schema = SeqrVariantSchema if self.dataset_type == 'VARIANTS' else SeqrSVSchema
        mt = Schema(mt).annotate_all().select_annotated_mt()

        mt.describe()
        mt.write(self.output().path)

    @staticmethod
    def validate_mt(mt, genome_version, sample_type):
        """
        Validate the mt by checking against a list of common coding and non-coding variants given its
        genome version. This validates genome_version, variants, and the reported sample type.

        :param mt: mt to validate
        :param genome_version: reference genome version
        :param sample_type: WGS or WES
        :return: True or Exception
        """
        sample_type_stats = HailMatrixTableTask.sample_type_stats(mt, genome_version)

        for name, stat in sample_type_stats.items():
            logger.info('Table contains %i out of %i common %s variants.' %
                        (stat['matched_count'], stat['total_count'], name))

        has_coding = sample_type_stats['coding']['match']
        has_noncoding = sample_type_stats['noncoding']['match']

        if not has_coding and not has_noncoding:
            # No common variants detected.
            raise SeqrValidationError(
                'Genome version validation error: dataset specified as GRCh{genome_version} but doesn\'t contain '
                'the expected number of common GRCh{genome_version} variants'.format(genome_version=genome_version)
            )
        elif has_noncoding and not has_coding:
            # Non coding only.
            raise SeqrValidationError(
                'Sample type validation error: Dataset contains noncoding variants but is missing common coding '
                'variants for GRCh{}. Please verify that the dataset contains coding variants.' .format(genome_version)
            )
        elif has_coding and not has_noncoding:
            # Only coding should be WES.
            if sample_type != 'WES':
                raise SeqrValidationError(
                    'Sample type validation error: dataset sample-type is specified as {} but appears to be '
                    'WGS because it contains many common coding variants'.format(sample_type)
                )
        elif has_noncoding and has_coding:
            # Both should be WGS.
            if sample_type != 'WGS':
                raise SeqrValidationError(
                    'Sample type validation error: dataset sample-type is specified as {} but appears to be '
                    'WES because it contains many common non-coding variants'.format(sample_type)
                )
        return True


class SeqrMTToESTask(HailElasticSearchTask):
    dest_file = luigi.Parameter()

    def requires(self):
        return [SeqrVCFToMTTask()]

    def output(self):
        # TODO: Use https://luigi.readthedocs.io/en/stable/api/luigi.contrib.esindex.html.
        return GCSorLocalTarget(filename=self.dest_file)

    def run(self):
        # Right now it writes to a file, but will export to ES in the future.
        mt = self.import_mt()
        with self.output().open('w') as out_file:
            out_file.write('count: %i' % mt.count()[0])


if __name__ == '__main__':
    luigi.run()
