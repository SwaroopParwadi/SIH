# SecureDoc Synthetic Dataset v1.0

Privacy-safe synthetic identity-document dataset for the SecureDoc AI SIH prototype.

This dataset contains NO real identity documents and is NOT an identity credential.

## Size
- Authentic: 1,000
- Manipulated: 1,000
- Total: 2,000

## Splits
- Train: 1,400 images (700 cases)
- Validation: 300 images (150 cases)
- Test: 300 images (150 cases)

## Manipulations
text_change, photo_change, number_change, date_change, copy_paste, clone, compression, mixed

## Files
- annotations/labels.csv
- annotations/metadata.csv
- annotations/regions.json
- preview/
- generate_dataset.py

## Recommended first task
Binary classification: AUTHENTIC vs MANIPULATED.

Use paired cases carefully: the same case is kept in only one split to prevent train/test leakage.

## Reproducibility
The generator uses fixed random seeds. The generated images in this package are the current dataset artifact.
