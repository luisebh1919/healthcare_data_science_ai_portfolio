-- Cancer concept set for the final project.
-- Source codes are SNOMED CT codes present in the Synthea condition data.
-- Suspected malignancies and carcinoma in situ are intentionally excluded.

WITH cancer_codes AS (
    SELECT * FROM (VALUES
        ('254837009', 'Malignant neoplasm of breast'),
        ('254637007', 'Non-small cell lung cancer'),
        ('424132000', 'Non-small cell carcinoma of lung, TNM stage 1'),
        ('363406005', 'Malignant neoplasm of colon'),
        ('109838007', 'Overlapping malignant neoplasm of colon'),
        ('93761005', 'Primary malignant neoplasm of colon'),
        ('93143009', 'Leukemia'),
        ('94503003', 'Metastatic malignant neoplasm to prostate'),
        ('94260004', 'Metastatic malignant neoplasm to colon'),
        ('67811000119102', 'Primary small cell malignant neoplasm of lung, TNM stage 1'),
        ('254632001', 'Small cell carcinoma of lung'),
        ('91861009', 'Acute myeloid leukemia')
    ) AS t(source_code, description)
)

SELECT *
FROM cancer_codes;
