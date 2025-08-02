import pandas as pd
from constants import COLUMNS_TYPES, FORD_SEDICI_MATERIAS,VALID_TYPES,LENGTH_DATASET

pd.set_option('display.max_colwidth', None)

def combine_non_nulls(row, values):
    non_nulls = [row[col] for col in values if pd.notna(row[col])]
    if not non_nulls:
        return None
    return non_nulls[0] if len(non_nulls) == 1 else non_nulls

def safe_split(value, delimiter, part=0):
    if isinstance(value, str) and delimiter in value:
        return value.split(delimiter)[part].strip()
    return value

def transform_uri(uri):
    if not isinstance(uri, str):
        return None
    try:
        main_uri = uri.split("||")[0]  # Quedarse con la parte de sedici
        return main_uri.split("handle/")[1].replace("/", "-")
    except Exception as e:
        print(f"uri mal formateado: {uri} - {e}")
        return None
    
def transform_subject(subject):
    if not isinstance(subject, str):
        return None
    try:
        key = safe_split(safe_split(subject, "||"), "::")
        return FORD_SEDICI_MATERIAS.get(key, None)
    except Exception as e:
        print(f"subject mal formateado: {subject} - {e}")
        return None

def transform_contributors(value):
    if not isinstance(value, str):
        return None
    try:
        elements = [safe_split(elem, "::") for elem in value.split("||")]
        return elements[0] if len(elements) == 1 else elements
    except Exception as e:
        print(f"contributor mal formateado: {value} - {e}")
        return None

def transform_institutions(value):
    if not isinstance(value, str):
        return None
    try:
        elements = [safe_split(elem, "::") for elem in value.split("||")]
        return ', '.join(elements) if elements else None
    except Exception as e:
        print(f"institution mal formateado: {value} - {e}")
        return None

def transform_degree(value):
    return safe_split(value, "::") if pd.notna(value) else None

def combine_title_subtitle(title, subtitle):
    if pd.notna(title) and pd.notna(subtitle):
        return f"{title}: {subtitle}"
    elif pd.notna(title):
        return title
    elif pd.notna(subtitle):
        return subtitle
    else:
        return None

def merge_data(csv_filename, filtered_csv_filename):
    df = pd.read_csv(csv_filename)

    # Match columns from COLUMNS_TYPES
    final_columns = {key: [col for col in df.columns if key in col] for key in COLUMNS_TYPES}
    selected_cols = [col for cols in final_columns.values() for col in cols]
    subset_df = df[selected_cols].copy()

    # 🔥 ELIMINAR DUPLICADOS EN LAS COLUMNAS
    subset_df = subset_df.loc[:, ~subset_df.columns.duplicated()]

    # Merge multiple columns
    for key, values in final_columns.items():
        if not values:
            continue
        if COLUMNS_TYPES[key]['cant'] == "unique":
            subset_df[key] = subset_df[values].ffill(axis=1).bfill(axis=1).iloc[:, 0]
            subset_df[key] = subset_df[key].where(subset_df[key].notnull(), None)
        else:
            subset_df[key] = subset_df.apply(lambda row: combine_non_nulls(row, values), axis=1)

    extra_cols = [col for col in selected_cols if col not in COLUMNS_TYPES]
    subset_df.drop(extra_cols, axis=1, inplace=True, errors='ignore')

    # 🔥 DELETE DUPLICATED COLUMNS
    subset_df = subset_df.loc[:, ~subset_df.columns.duplicated()]

    subset_df['dc.date.issued'] = pd.to_datetime(subset_df['dc.date.issued'], errors='coerce')
    subset_df = subset_df[subset_df['dc.date.issued'].dt.year > 2018]

    subset_df = subset_df[subset_df['dc.type'].isin(VALID_TYPES)]

    subset_df["not_null_count"] = subset_df.notnull().sum(axis=1)
    subset_df = subset_df.sort_values(by='not_null_count', ascending=False).drop(columns=['not_null_count'])

    subset_df['id'] = subset_df['dc.identifier.uri'].apply(transform_uri)

    for degree_col in ["thesis.degree.name", "thesis.degree.grantor"]:
        subset_df[degree_col] = subset_df[degree_col].apply(transform_degree)

    subset_df['sedici.subject.materias'] = subset_df['sedici.subject.materias'].apply(transform_subject)

    contributor_cols = [
        "sedici.contributor.compiler", "sedici.contributor.director",
        "sedici.contributor.codirector", "sedici.creator.person",
        "sedici.contributor.colaborator"
    ]
    for col in contributor_cols:
        subset_df[col] = subset_df[col].apply(transform_contributors)

    institution_cols = ["mods.originInfo.place", "sedici.institucionDesarrollo"]
    for col in institution_cols:
        subset_df[col] = subset_df[col].apply(transform_institutions)

    subset_df["dc.subject"] = subset_df["dc.subject"].apply(lambda x: x.split("||") if isinstance(x, str) else None)

    # Combine title and subtitle
    subset_df['dc.title'] = subset_df.apply(lambda row: combine_title_subtitle(row['dc.title'], row.get('sedici.title.subtitle')), axis=1)
    
    # Remove subtitle column since it's now combined with title
    if 'sedici.title.subtitle' in subset_df.columns:
        subset_df = subset_df.drop('sedici.title.subtitle', axis=1)

    print("guardando csv")
    subset_df.to_csv(filtered_csv_filename, index=False)
    print("terminado")


def get_ids_from_csv(csv_file, extra_objetos=200):
    df = pd.read_csv(csv_file)
    base_ids = df["id"].dropna().tolist()[:LENGTH_DATASET]


    extra_df = df[
        (df["dc.type"] == "Objeto de conferencia") &
        (~df["id"].isin(base_ids))
    ].dropna(subset=["id"]).drop_duplicates(subset=["id"]).head(extra_objetos)

    final_ids = base_ids + extra_df["id"].tolist()
    final_df = df[df["id"].isin(final_ids)]

    return final_df["id"].tolist()

