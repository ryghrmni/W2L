# app.py
# ------------------------------------------------------------
# Streamlit app: Professional wide→long (melt) transformer (English UI)
# Now includes a full "Guide & Instructions" tab with step-by-step docs
# ------------------------------------------------------------

import io
from datetime import datetime

import pandas as pd
import streamlit as st

# ----------------------------
# Page Config & Global Styles
# ----------------------------
st.set_page_config(
    page_title="Wide→Long Transformer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
:root {
  --brand-1: #3b82f6; /* blue-500 */
  --brand-2: #8b5cf6; /* violet-500 */
  --bg-gradient: linear-gradient(135deg, rgba(59,130,246,0.08), rgba(139,92,246,0.08));
}
.block-container {padding-top: 2rem !important;}
.main-header { background: var(--bg-gradient); border: 1px solid rgba(0,0,0,0.06); padding: 1.25rem; border-radius: 18px; }
.kpi { border-radius: 16px; padding: 1.1rem; border: 1px solid rgba(0,0,0,0.08); background: white; box-shadow: 0 6px 18px rgba(0,0,0,0.04);} 
.download-card { border-radius: 16px; padding: 1rem; border: 1px dashed rgba(0,0,0,0.15);} 
.stButton>button { border-radius: 12px; border: 1px solid rgba(0,0,0,0.1); padding: 0.6rem 1rem; font-weight: 600; background: linear-gradient(135deg, #ffffff, #f7f7ff);} 
.ol {counter-reset: item;}
.ol li{list-style:none; margin: .4rem 0;}
.ol li:before{content: counters(item, ".") ". "; counter-increment:item; font-weight:600;}
code {background: #f6f8fa; padding: 2px 6px; border-radius: 6px;}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ----------------------------
# Sidebar - About & Settings
# ----------------------------
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.markdown("---")
    st.markdown(
        """
        **About**  
        This app converts wide tables to long format (like `pandas.melt`).  
        Typical use: choose an **ID column** (e.g., `data`) and unpivot value columns (`col1..colN`).
        """
    )
    st.caption("Built with ❤️ using Streamlit & Pandas")

# ----------------------------
# Helpers
# ----------------------------
@st.cache_data(show_spinner=False)
def load_excel(file_bytes: bytes, sheet_name=None) -> pd.DataFrame:
    if sheet_name is None:
        return pd.read_excel(io.BytesIO(file_bytes))
    else:
        return pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)

@st.cache_data(show_spinner=False)
def list_sheets(file_bytes: bytes):
    x = pd.ExcelFile(io.BytesIO(file_bytes))
    return x.sheet_names

def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Transformed") -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

def build_sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "data": ["x", "y", "z"],
        "col1": ["px1", "py1", "pz1"],
        "col2": ["px2", "py2", "pz2"],
        "col3": ["px3", "py3", "pz3"],
    })

# ----------------------------
# Header
# ----------------------------
col_a, col_b = st.columns([0.65, 0.35])
with col_a:
    st.markdown(
        f"""
        <div class="main-header">
        <h1 style="margin:0">📈 Wide→Long Professional Transformer</h1>
        <p style="margin:6px 0 0 0; opacity:0.8">Upload an Excel/CSV file, pick the ID column, and melt to long format in a few clicks.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_b:
    st.markdown("")
    st.metric(label="Today", value=datetime.now().strftime("%Y-%m-%d"))

st.markdown("")

# ============================
# Tabs: Transform | Guide
# ============================
TAB_TRANSFORM, TAB_GUIDE = st.tabs(["🔧 Transform", "📘 Guide & Instructions"])

with TAB_TRANSFORM:
    # ----------------------------
    # Uploader & Preview
    # ----------------------------
    left, right = st.columns([0.6, 0.4])
    with left:
        st.subheader("1) Upload File")
        file = st.file_uploader("Upload an Excel or CSV file", type=["xlsx", "xls", "csv"])    

        # Sample/template
        with st.expander("Sample / Template", expanded=False):
            demo_df = build_sample_df()
            st.dataframe(demo_df, use_container_width=True)
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("Download as CSV", demo_df.to_csv(index=False).encode('utf-8'), file_name="sample_wide.csv")
            with c2:
                st.download_button("Download as Excel", to_excel_bytes(demo_df), file_name="sample_wide.xlsx")
            if st.button("Use this sample"):
                st.session_state["_demo_df"] = demo_df.copy()

    with right:
        st.subheader("Preview")
        df = None
        sheet_name = None

        if file is not None:
            name = file.name.lower()
            try:
                if name.endswith(".csv"):
                    df = pd.read_csv(file)
                else:
                    excel_bytes = file.read()
                    sheets = list_sheets(excel_bytes)
                    if len(sheets) > 1:
                        sheet_name = st.selectbox("Select Excel sheet", sheets)
                    df = load_excel(excel_bytes, sheet_name)
            except Exception as e:
                st.error("Error reading file: " + str(e))

        if df is None and "_demo_df" in st.session_state:
            df = st.session_state["_demo_df"].copy()

        if df is not None:
            st.dataframe(df.head(100), use_container_width=True)
            st.caption("(showing first 100 rows)")
        else:
            st.info("Upload a file or use the sample to get started.")

    # ----------------------------
    # Melt Controls
    # ----------------------------
    if 'df' in locals() and df is not None:
        st.markdown("---")
        st.subheader("2) Transform Settings")

        cols = list(df.columns)
        if not cols:
            st.stop()

        id_col = st.selectbox("ID column", options=cols, index=0)
        value_cols = st.multiselect(
            "Columns to unpivot",
            options=[c for c in cols if c != id_col],
            default=[c for c in cols if c != id_col],
        )
        var_name = st.text_input("Variable column name", value="column")
        value_name = st.text_input("Value column name", value="value")

        copt1, copt2, copt3 = st.columns(3)
        with copt1:
            dropna = st.checkbox("Drop NA", value=True)
        with copt2:
            strip_ws = st.checkbox("Trim whitespace", value=True)
        with copt3:
            keep_order = st.checkbox("Keep ID order", value=True)

        st.markdown("")
        go = st.button("🚀 Run Transform", use_container_width=True)

        if go:
            work = df.copy()
            if strip_ws:
                for c in work.columns:
                    if pd.api.types.is_string_dtype(work[c]):
                        work[c] = work[c].astype(str).str.strip()
            if not value_cols:
                st.warning("Pick at least one column to unpivot.")
                st.stop()
            try:
                melted = pd.melt(
                    work,
                    id_vars=[id_col],
                    value_vars=value_cols,
                    var_name=var_name,
                    value_name=value_name,
                )
                if dropna:
                    melted = melted.dropna(subset=[value_name])
                if keep_order:
                    # preserve original order of IDs
                    id_cat = pd.Categorical(
                        melted[id_col],
                        categories=list(work[id_col].drop_duplicates()),
                        ordered=True,
                    )
                    melted[id_col] = id_cat
                    melted = melted.sort_values([id_col, var_name]).reset_index(drop=True)

                st.success("Transform completed successfully!")

                st.markdown("#### Output (Long)")
                st.dataframe(melted, use_container_width=True)

                # Downloads
                csv_bytes = melted.to_csv(index=False).encode("utf-8")
                xlsx_bytes = to_excel_bytes(melted)

                d1, d2, d3 = st.columns(3)
                with d1:
                    st.download_button("⬇️ Download CSV", csv_bytes, file_name="transformed_long.csv")
                with d2:
                    st.download_button("⬇️ Download Excel", xlsx_bytes, file_name="transformed_long.xlsx")
                with d3:
                    st.download_button(
                        "⬇️ Download JSON",
                        melted.to_json(orient="records").encode("utf-8"),
                        file_name="transformed_long.json",
                    )

                # Quick stats
                st.markdown("---")
                k1, k2, k3 = st.columns(3)
                with k1:
                    st.markdown(f"<div class='kpi'><b>Rows</b><br>{len(melted):,}</div>", unsafe_allow_html=True)
                with k2:
                    st.markdown(f"<div class='kpi'><b>Unique IDs</b><br>{melted[id_col].nunique():,}</div>", unsafe_allow_html=True)
                with k3:
                    st.markdown(f"<div class='kpi'><b>Variables</b><br>{len(value_cols):,}</div>", unsafe_allow_html=True)

            except Exception as e:
                st.error("Transform error: " + str(e))

with TAB_GUIDE:
    st.subheader("How the App Works — Complete Guide")

    st.markdown("""
This application **unpivots** a wide table to a long format using `pandas.melt`. It is ideal when you have one **ID column** (e.g., `data`) and multiple **value columns** (e.g., `col1`, `col2`, `col3`).

**Example input (wide):**

```
data  col1  col2  col3
x     px1   px2   px3
y     py1   py2   py3
z     pz1   pz2   pz3
```

**Output (long):**

```
data  column  value
x     col1    px1
x     col2    px2
x     col3    px3
y     col1    py1
y     col2    py2
y     col3    py3
z     col1    pz1
z     col2    pz2
z     col3    pz3
```
""")

    with st.expander("Step-by-step walkthrough"):
        st.markdown(
            """
<ol class="ol">
<li><b>Upload</b>: Upload your file (Excel: .xlsx/.xls, or .csv). If your Excel has multiple sheets, pick the relevant sheet.</li>
<li><b>Preview</b>: Verify the first 100 rows to ensure the header row and data types look correct.</li>
<li><b>Select ID column</b>: Choose the column that identifies each row (e.g., <code>data</code>).</li>
<li><b>Choose columns to unpivot</b>: Pick the wide columns (e.g., <code>col1</code>, <code>col2</code>, ...). These will turn into rows.</li>
<li><b>Set output column names</b>: Provide names for the new <i>variable</i> and <i>value</i> columns (defaults: <code>column</code>, <code>value</code>).</li>
<li><b>Options</b>:
  <ul>
    <li><b>Drop NA</b>: Remove rows where the value is missing.</li>
    <li><b>Trim whitespace</b>: Strip extra spaces from string columns before melting.</li>
    <li><b>Keep ID order</b>: Preserve the original order of IDs in the result.</li>
  </ul>
</li>
<li><b>Run Transform</b>: Click to execute. The app shows the long table and lets you download CSV/Excel/JSON.</li>
<li><b>Review KPIs</b>: Quick stats summarize rows, unique IDs, and number of variables.</li>
</ol>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("Under the hood (pandas.melt)", expanded=False):
        st.markdown(
            """
The transformation is equivalent to:

```python
import pandas as pd
melted = pd.melt(
    df,
    id_vars=["data"],            # your ID column
    value_vars=["col1","col2","col3"],  # columns to unpivot
    var_name="column",
    value_name="value",
)
```
Additional post-processing is applied based on options (drop NAs, trimming strings, preserving ID order).
            """
        )

    with st.expander("Data requirements & best practices"):
        st.markdown(
            """
- The first row should be headers. If not, clean your file so the intended headers are in row 1.
- Your **ID column** should uniquely identify each record (or group of records) before the melt. Duplicates are allowed but will repeat accordingly.
- Wide columns should be homogeneous (e.g., all prices, or all labels), otherwise the long output may mix different concepts.
- For large files, prefer CSV for faster loading. Keep your browser tab open while processing.
            """
        )

    with st.expander("Troubleshooting & FAQs"):
        st.markdown(
            """
**Q: My Excel has multiple sheets. Which one is used?**  
A: If there are multiple sheets, the app prompts you to select one.

**Q: I see strange spaces or mismatches.**  
A: Enable **Trim whitespace** before running. This strips extra spaces in string columns.

**Q: I only need some columns melted.**  
A: Use **Columns to unpivot** and select only those you want.

**Q: The order of IDs changed.**  
A: Toggle **Keep ID order** to preserve the original order.

**Q: How do I save results?**  
A: Use the **Download** buttons (CSV, Excel, JSON) after the transform.

**Q: Can I rename output columns?**  
A: Yes. Set **Variable column name** and **Value column name** (defaults: <code>column</code>, <code>value</code>).
            """
        )

    with st.expander("Deployment tips"):
        st.markdown(
            """
- Run locally: `streamlit run app.py`
- Requirements: `pip install streamlit pandas xlsxwriter`
- For servers (e.g., Streamlit Community Cloud, Docker, or internal VM):
  - Create a `requirements.txt` with the above packages.
  - If using Docker, expose port 8501 and set the command to `streamlit run app.py --server.port 8501 --server.address 0.0.0.0`.
- Security: This demo processes files in-memory per session and does not persist them server-side.
            """
        )

# ----------------------------
# Footer
# ----------------------------

st.markdown(
    """
---
Provided by: Reza Ghahremani - Melchioni S.P.A - Digital Innovation
"""
)
