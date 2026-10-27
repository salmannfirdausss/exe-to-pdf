import os
import streamlit as st
from converter import exe_to_pdf, ConvertError

st.set_page_config(page_title="EXE ke PDF", page_icon="📄")
st.title("📄 EXE → PDF")
st.caption("Ubah PDF yang dibungkus jadi .exe (Vaysoft PDF to EXE) menjadi PDF biasa. "
           "File exe tidak dijalankan, hanya dibaca.")

up = st.file_uploader("Upload file .exe", type=["exe"])
if up is not None:
    with st.spinner("Mengonversi..."):
        try:
            pdf = exe_to_pdf(up.getvalue())
        except ConvertError as e:
            st.error(str(e))
            pdf = None
        except Exception:
            st.error("Terjadi kesalahan saat memproses file.")
            pdf = None
    if pdf:
        name = os.path.splitext(up.name)[0] + ".pdf"
        st.success(f"Berhasil: {len(pdf)/1024:.0f} KB")
        st.download_button("⬇️ Download PDF", pdf, file_name=name, mime="application/pdf")
