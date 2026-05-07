# Pipeline flow, as of 05/06/2026

```
                      WriteImportedCallsetTask
                      (VCF → Hail Matrix Table)
                                |
                                v
                   WritePostprocessedCallsetTask
                   (split multi, deduplicate)
                                |
                                v
                       ValidateCallsetTask
                       (validation checks)
                                |
                 _______________|_______________
                |                               |
                v                               v
    WriteSexCheckTableTask    WriteRelatednessCheckTableTask
                |                               |
                v                               v
                         WriteRelatednessCheckTsvTask
                                |
                                v
           _____________________|_____________________
          |                                           |
          v                                           v
  WriteRemappedAndSubsettedCallsetTask  WriteRemappedAndSubsettedCallsetTask
    (Project 1)                            (Project N)
          |                                           |
          |___________________________________________|
                                |
                                v
                   WriteMetadataForRunTask
                                |
                                v
                    WriteNewVariantsTableTask
                                |
                                v
            UpdateVariantAnnotationsTableWithNewVariantsTask
                      (Variants with annotations)
                                |
          ______________________+_______________________
          |                     |                      |
          v                     v                      v
  WriteNewEntries...     WriteNewVariants...    WriteNewVariantDetails...
  ParquetTask            ParquetTask            ParquetTask
  |                      |                      (optional)
  |  [also requires]     |  [or just]
  |  RemappedCallsets    |  WriteNewVariantsTableTask
  |
  |_______________________|
          |
          v
     RunPipelineTask
     (all parquets ready)
          |
          v
    WriteSuccessFileTask
          |
          v
  WriteClickhouseLoadSuccessFileTask
  (load parquets → ClickHouse)
```