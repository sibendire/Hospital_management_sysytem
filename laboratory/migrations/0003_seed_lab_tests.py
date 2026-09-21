from decimal import Decimal

from django.db import migrations


# =========================================================
# STANDARD LABORATORY TESTS
# =========================================================

LAB_TESTS = [

    {
        "name": "Full Blood Count (FBC)",
        "category": "Hematology",
        "price": Decimal("0.00"),
        "description": (
            "Complete blood count used to assess red blood cells, "
            "white blood cells, hemoglobin and platelets."
        ),
    },

    {
        "name": "Blood Group",
        "category": "Hematology",
        "price": Decimal("0.00"),
        "description": (
            "Determines the patient's ABO blood group and Rh factor."
        ),
    },

    {
        "name": "Malaria Test",
        "category": "Parasitology",
        "price": Decimal("0.00"),
        "description": (
            "Laboratory examination for malaria parasites."
        ),
    },

    {
        "name": "HIV Test",
        "category": "Immunology",
        "price": Decimal("0.00"),
        "description": (
            "Laboratory test used for HIV screening."
        ),
    },

    {
        "name": "Urinalysis",
        "category": "Urinalysis",
        "price": Decimal("0.00"),
        "description": (
            "Routine examination of urine for physical, "
            "chemical and microscopic abnormalities."
        ),
    },

    {
        "name": "Stool Analysis",
        "category": "Parasitology",
        "price": Decimal("0.00"),
        "description": (
            "Laboratory examination of stool for parasites "
            "and other abnormalities."
        ),
    },

    {
        "name": "Blood Sugar / Glucose",
        "category": "Chemistry",
        "price": Decimal("0.00"),
        "description": (
            "Measurement of blood glucose levels."
        ),
    },

    {
        "name": "Liver Function Test (LFT)",
        "category": "Chemistry",
        "price": Decimal("0.00"),
        "description": (
            "Panel of laboratory tests used to assess liver function."
        ),
    },

    {
        "name": "Kidney/Renal Function Test (RFT)",
        "category": "Chemistry",
        "price": Decimal("0.00"),
        "description": (
            "Laboratory tests used to assess kidney function."
        ),
    },

    {
        "name": "Widal Test",
        "category": "Immunology",
        "price": Decimal("0.00"),
        "description": (
            "Serological test used in the investigation "
            "of suspected typhoid infection."
        ),
    },

    {
        "name": "Pregnancy Test",
        "category": "Immunology",
        "price": Decimal("0.00"),
        "description": (
            "Laboratory test for detection of human chorionic "
            "gonadotropin (hCG)."
        ),
    },

    {
        "name": "Hepatitis B Test",
        "category": "Immunology",
        "price": Decimal("0.00"),
        "description": (
            "Laboratory screening for hepatitis B infection."
        ),
    },

    {
        "name": "Hepatitis C Test",
        "category": "Immunology",
        "price": Decimal("0.00"),
        "description": (
            "Laboratory screening for hepatitis C infection."
        ),
    },

    {
        "name": "HIV Viral Load",
        "category": "Immunology",
        "price": Decimal("0.00"),
        "description": (
            "Measurement of HIV RNA in the patient's blood."
        ),
    },

    {
        "name": "CD4 Count",
        "category": "Immunology",
        "price": Decimal("0.00"),
        "description": (
            "Measurement of CD4 T-lymphocyte count."
        ),
    },

    {
        "name": "Serum Creatinine",
        "category": "Chemistry",
        "price": Decimal("0.00"),
        "description": (
            "Measurement of serum creatinine used in assessment "
            "of kidney function."
        ),
    },

    {
        "name": "Urea",
        "category": "Chemistry",
        "price": Decimal("0.00"),
        "description": (
            "Measurement of blood urea concentration."
        ),
    },

    {
        "name": "Electrolytes",
        "category": "Chemistry",
        "price": Decimal("0.00"),
        "description": (
            "Measurement of important electrolytes such as sodium "
            "and potassium."
        ),
    },

    {
        "name": "Lipid Profile",
        "category": "Chemistry",
        "price": Decimal("0.00"),
        "description": (
            "Blood test measuring major lipid parameters."
        ),
    },

    {
        "name": "HbA1c",
        "category": "Chemistry",
        "price": Decimal("0.00"),
        "description": (
            "Measurement of glycated hemoglobin used to assess "
            "average blood glucose over time."
        ),
    },

    {
        "name": "ESR",
        "category": "Hematology",
        "price": Decimal("0.00"),
        "description": (
            "Erythrocyte sedimentation rate test used as a "
            "general marker of inflammation."
        ),
    },

    {
        "name": "Blood Film",
        "category": "Hematology",
        "price": Decimal("0.00"),
        "description": (
            "Microscopic examination of a peripheral blood smear."
        ),
    },

    {
        "name": "Sputum Test",
        "category": "Microbiology",
        "price": Decimal("0.00"),
        "description": (
            "Laboratory examination of sputum specimens."
        ),
    },

    {
        "name": "Culture and Sensitivity",
        "category": "Microbiology",
        "price": Decimal("0.00"),
        "description": (
            "Laboratory culture used to identify microorganisms "
            "and assess antimicrobial susceptibility."
        ),
    },
]


# =========================================================
# CREATE LABORATORY TESTS
# =========================================================

def create_lab_tests(apps, schema_editor):

    LabTest = apps.get_model(
        "laboratory",
        "LabTest"
    )

    for test in LAB_TESTS:

        LabTest.objects.get_or_create(
            name=test["name"],
            defaults={
                "category": test["category"],
                "price": test["price"],
                "description": test["description"],
            },
        )


# =========================================================
# REMOVE SEEDED TESTS IF MIGRATION IS REVERSED
# =========================================================

def remove_lab_tests(apps, schema_editor):

    LabTest = apps.get_model(
        "laboratory",
        "LabTest"
    )

    names = [
        test["name"]
        for test in LAB_TESTS
    ]

    LabTest.objects.filter(
        name__in=names
    ).delete()


# =========================================================
# MIGRATION
# =========================================================

class Migration(migrations.Migration):

    dependencies = [
        (
            "laboratory",
            "0002_alter_labrequest_options_alter_labresult_options_and_more",
        ),
    ]

    operations = [

        migrations.RunPython(
            create_lab_tests,
            remove_lab_tests,
        ),

    ]