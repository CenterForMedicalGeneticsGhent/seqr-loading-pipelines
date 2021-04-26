import gzip
import logging
import os
import pickle
from tqdm import tqdm

from sv_pipeline.genome.utils.download_utils import download_file

GENOME_VERSION_GRCh37 = "37"
GENOME_VERSION_GRCh38 = "38"

logger = logging.getLogger(__name__)

GENCODE_GTF_URL = "http://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_{gencode_release}/gencode.v{gencode_release}.annotation.gtf.gz"

# expected GTF file header
GENCODE_FILE_HEADER = [
    'chrom', 'source', 'feature_type', 'start', 'end', 'score', 'strand', 'phase', 'info'
]


def load_gtf_data(gene_id_mapping, gencode_gtf_path):
    root, ext = os.path.splitext(gencode_gtf_path)
    pickle_file = root + '.pickle'
    if os.path.isfile(pickle_file):
        logger.info('Use the existing pickle file {}.\nIf you want to reload the data, please delete it and re-run the data loading'.format(pickle_file))
        with open(pickle_file, 'rb') as handle:
            p = pickle.load(handle)
        gene_id_mapping.update(p)
        return

    with gzip.open(gencode_gtf_path, 'rt') as gencode_file:
        for i, line in enumerate(tqdm(gencode_file, unit=' gencode records')):
            line = line.rstrip('\r\n')
            if not line or line.startswith('#'):
                continue
            fields = line.split('\t')

            if len(fields) != len(GENCODE_FILE_HEADER):
                raise ValueError("Unexpected number of fields on line #%s: %s" % (i, fields))

            record = dict(zip(GENCODE_FILE_HEADER, fields))

            if record['feature_type'] != 'gene':
                continue

            # parse info field
            info_fields = [x.strip().split() for x in record['info'].split(';') if x != '']
            info_fields = {k: v.strip('"') for k, v in info_fields}

            gene_id_mapping[info_fields['gene_name']] = info_fields['gene_id'].split('.')[0]

    with open(pickle_file, 'wb') as handle:
        pickle.dump(gene_id_mapping, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_gencode(gencode_release, gencode_gtf_path=None, download_path=None):
    """Load Gencode to create a gene symbols to gene ids mapping table.

    Args:
        gencode_release (int): the gencode release to load (eg. 25)
        gencode_gtf_path (str): optional local file path of gencode GTF file. If not provided, it will be downloaded.
        download_path (str): The path for downloaded data
    """
    gene_id_mapping = {}

    if not gencode_gtf_path or not os.path.isfile(gencode_gtf_path):
        url = GENCODE_GTF_URL.format(gencode_release=gencode_release)
        gencode_gtf_path = download_file(url, to_dir=download_path)

    logger.info("Loading {}".format(gencode_gtf_path))
    load_gtf_data(gene_id_mapping, gencode_gtf_path)

    logger.info('Get {} gene id mapping records'.format(len(gene_id_mapping)))
    return gene_id_mapping
