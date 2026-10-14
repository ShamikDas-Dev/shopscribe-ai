from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

from core.generator import DEFAULT_GROQ_MODEL, DEFAULT_LOCAL_MODEL, generate_content, list_local_models
from core.pricing import calculate_discount_percent
from core.schemas import ContentPack, ProductFacts
from core.validators import validate_content_pack
from storage.history import DEFAULT_DB_PATH, get_recent_history, save_history

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_FILE = BASE_DIR / "sample_data" / "cosmetics_demo.json"

st.set_page_config(
    page_title="ShopScribe AI",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

def get_groq_api_key() -> str:
    """Read the Groq key from Streamlit secrets or a local environment variable."""
    try:
        value = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        value = ""
    return str(value or os.getenv("GROQ_API_KEY", "")).strip()


def get_bool_setting(name: str, default: bool = False) -> bool:
    """Read a boolean from Streamlit secrets or an environment variable."""
    try:
        value = st.secrets.get(name, os.getenv(name, default))
    except Exception:
        value = os.getenv(name, default)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


GROQ_API_KEY = get_groq_api_key()
# Set this to true in Streamlit Cloud so one server-side SQLite history is not
# shared with every visitor. It defaults to false for local runs.
DISABLE_SERVER_HISTORY = get_bool_setting("SHOPSCRIBE_DISABLE_SERVER_HISTORY", False)

if DISABLE_SERVER_HISTORY:
    # Remove history left by earlier deployments. New hosted sessions will neither
    # write nor read a shared history database while this flag is enabled.
    for suffix in ("", "-wal", "-shm"):
        try:
            Path(f"{DEFAULT_DB_PATH}{suffix}").unlink(missing_ok=True)
        except OSError:
            # History remains disabled even if the host prevents cleanup.
            pass
PROVIDERS = ["Ollama (local)", "Groq API (cloud)"]
default_provider_index = 1 if GROQ_API_KEY else 0

st.title("ShopScribe AI")
st.caption("AI marketing assistant for independent retailers")
st.write(
    "Turn verified product details into editable Instagram captions, WhatsApp "
    "promotions, and catalogue descriptions. Choose local or hosted open-weight inference."
)

with st.sidebar:
    st.header("AI settings")
    provider_choice = st.selectbox(
        "AI provider",
        PROVIDERS,
        index=default_provider_index,
        help="Use Ollama for private local generation or Groq for a public cloud deployment.",
    )
    if provider_choice == "Groq API (cloud)":
        provider = "Groq"
        model_name = st.selectbox(
            "Groq model",
            ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"],
            index=0,
            help="Use an available model in your Groq account. GPT-OSS 20B is the default; try Qwen for Bengali.",
        )
        ollama_host = "http://127.0.0.1:11434"
        if GROQ_API_KEY:
            st.success("Groq API key configured")
        else:
            st.warning(
                "Groq key missing. Add GROQ_API_KEY to Streamlit Community Cloud → "
                "App settings → Secrets. Never put the key in GitHub or in this source code."
            )
        st.caption(
            "Cloud mode sends product facts to Groq for generation. The provider's free limits, "
            "model availability, and pricing can change."
        )
    else:
        provider = "Ollama"
        model_name = st.text_input(
            "Ollama model",
            value=DEFAULT_LOCAL_MODEL,
            help="Use an installed model, such as qwen3:4b. For Bengali, you can also test gemma3:4b.",
        )
        ollama_host = st.text_input("Ollama host", value="http://127.0.0.1:11434")
        if st.button("Check local models", use_container_width=True):
            try:
                installed = list_local_models(host=ollama_host)
                if installed:
                    st.success("Installed models: " + ", ".join(installed))
                else:
                    st.warning(f"Ollama is reachable, but no models were found. Run `ollama pull {DEFAULT_LOCAL_MODEL}`.")
            except RuntimeError as exc:
                st.error(str(exc))
        st.caption(
            "With local Ollama, product facts are processed by the model running on the configured Ollama server. "
            "The local SQLite history is not guaranteed to persist on cloud hosts."
        )

if "last_pack" not in st.session_state:
    st.session_state.last_pack = None
if "last_product_name" not in st.session_state:
    st.session_state.last_product_name = ""
if "last_mrp" not in st.session_state:
    st.session_state.last_mrp = None
if "last_selling_price" not in st.session_state:
    st.session_state.last_selling_price = None

with st.expander("Load example product", expanded=False):
    st.caption("Use this sample to test the workflow. Replace these facts with verified details before using generated content commercially.")
    if st.button("Load cosmetics example"):
        try:
            example = json.loads(SAMPLE_FILE.read_text(encoding="utf-8"))
            # Set widget state before the form widgets are created in this run.
            st.session_state["product_name_input"] = example.get("product_name", "")
            st.session_state["brand_input"] = example.get("brand", "")
            st.session_state["category_input"] = example.get("category", "Skincare")
            st.session_state["selling_price_input"] = str(example.get("selling_price", ""))
            st.session_state["mrp_input"] = str(example.get("mrp", ""))
            st.session_state["features_input"] = example.get("features_text", "")
            st.session_state["audience_input"] = example.get("target_audience", "Everyday shoppers")
            st.session_state["tone_input"] = example.get("tone", "Friendly")
            st.rerun()
        except (OSError, json.JSONDecodeError) as exc:
            st.error(f"Could not load example: {exc}")

st.subheader("1. Product facts")
language = "English"  # Output language is fixed; the language selector was removed.
with st.form("product_form", clear_on_submit=False):
    left, right = st.columns(2)
    with left:
        product_name = st.text_input("Product name *", value="", max_chars=120, key="product_name_input")
        brand = st.text_input("Brand (optional)", value="", max_chars=100, key="brand_input")
        category = st.text_input("Category", value="Skincare", max_chars=80, key="category_input")
        selling_price_text = st.text_input("Selling price in ₹ (optional)", value="", help="Enter digits only, for example 299 or 249.50.", key="selling_price_input")
        mrp_text = st.text_input("MRP in ₹ (optional)", value="", help="Optional. Used only for a discount calculation when both prices are provided.", key="mrp_input")
    with right:
        features_text = st.text_area(
            "Verified product facts *",
            value="",
            height=150,
            max_chars=2000,
            placeholder="One fact per line, such as: Lightweight texture\n50 g pack\nContains glycerin (only if confirmed on label)",
            key="features_input",
        )
        audience = st.text_input("Target customer", value="Everyday shoppers", max_chars=120, key="audience_input")
        tone = st.selectbox("Tone", ["Friendly", "Professional", "Festive", "Minimal"], index=0, key="tone_input")

    submitted = st.form_submit_button("Generate content pack", type="primary", use_container_width=True)

if submitted:
    errors: list[str] = []
    if not product_name.strip():
        errors.append("Product name is required.")
    feature_lines = [line.strip() for line in features_text.splitlines() if line.strip()]
    if not feature_lines:
        errors.append("Enter at least one verified product fact.")

    def parse_optional_price(value: str, label: str) -> float | None:
        if not value.strip():
            return None
        try:
            parsed = float(value.replace(",", "").strip())
            if parsed <= 0:
                raise ValueError
            return parsed
        except ValueError:
            errors.append(f"{label} must be a positive number, for example 299.")
            return None

    selling_price = parse_optional_price(selling_price_text, "Selling price")
    mrp = parse_optional_price(mrp_text, "MRP")
    if selling_price is not None and mrp is not None and selling_price > mrp:
        errors.append("Selling price cannot be greater than MRP. Check the values.")

    if errors:
        for error in errors:
            st.error(error)
    else:
        try:
            facts = ProductFacts(
                product_name=product_name.strip(),
                brand=brand.strip() or None,
                category=category.strip() or "General",
                verified_features=feature_lines,
                target_audience=audience.strip() or "General shoppers",
                selling_price=selling_price,
                mrp=mrp,
            )
            spinner_text = "Generating with Groq cloud inference..." if provider == "Groq" else "Generating with your local model..."
            with st.spinner(spinner_text):
                pack = generate_content(
                    facts=facts,
                    language=language,
                    tone=tone,
                    model=model_name.strip() or (DEFAULT_GROQ_MODEL if provider == "Groq" else DEFAULT_LOCAL_MODEL),
                    host=ollama_host.strip() or "http://127.0.0.1:11434",
                    provider=provider,
                    api_key=GROQ_API_KEY if provider == "Groq" else None,
                )
                deterministic_notes = validate_content_pack(pack, facts)
                pack.review_notes = list(dict.fromkeys(pack.review_notes + deterministic_notes))
                for edit_key in ("edit_product_title", "edit_product_description", "edit_instagram", "edit_whatsapp", "edit_hashtags", "copy_text"):
                    st.session_state.pop(edit_key, None)
                st.session_state.last_pack = pack.model_dump()
                st.session_state.last_product_name = facts.product_name
                st.session_state.last_mrp = mrp
                st.session_state.last_selling_price = selling_price
                if not DISABLE_SERVER_HISTORY:
                    save_history(
                        product_name=facts.product_name,
                        language=language,
                        model=f"{provider}:{model_name.strip() or (DEFAULT_GROQ_MODEL if provider == 'Groq' else DEFAULT_LOCAL_MODEL)}",
                        content_json=pack.model_dump_json(),
                    )
            st.success("Content pack generated.")
        except Exception as exc:
            st.error(f"Generation failed: {exc}")
            if provider == "Groq":
                st.info("Check GROQ_API_KEY in your deployment secrets, confirm the selected model is enabled for your account, and review Groq's current rate limits.")
            else:
                st.info("Check that Ollama is running and that the selected model has been downloaded. In a terminal, try `ollama list` and `ollama run qwen3:4b`.")

pack_data = st.session_state.get("last_pack")
if pack_data:
    try:
        pack = ContentPack.model_validate(pack_data)
        st.divider()
        st.subheader(f"2. Generated content: {st.session_state.get('last_product_name', '')}")
        if pack.review_notes:
            st.warning("Review before publishing")
            for note in pack.review_notes:
                st.write(f"- {note}")
        tabs = st.tabs(["Product listing", "Instagram", "WhatsApp", "Hashtags"])
        with tabs[0]:
            st.text_input("Product title", value=pack.product_title, key="edit_product_title")
            st.text_area("Product description", value=pack.product_description, height=180, key="edit_product_description")
            st.button("Prepare listing for copying", key="copy_listing", on_click=lambda: st.session_state.update(copy_text=st.session_state.get("edit_product_title", "") + "\n\n" + st.session_state.get("edit_product_description", "")))
        with tabs[1]:
            st.text_area("Instagram caption", value=pack.instagram_caption, height=220, key="edit_instagram")
            st.button("Prepare caption for copying", key="copy_instagram", on_click=lambda: st.session_state.update(copy_text=st.session_state.get("edit_instagram", "")))
        with tabs[2]:
            st.text_area("WhatsApp message", value=pack.whatsapp_message, height=180, key="edit_whatsapp")
            st.button("Prepare message for copying", key="copy_whatsapp", on_click=lambda: st.session_state.update(copy_text=st.session_state.get("edit_whatsapp", "")))
        with tabs[3]:
            st.text_area("Hashtags", value=" ".join(pack.hashtags), height=120, key="edit_hashtags")
            st.button("Prepare hashtags for copying", key="copy_hashtags", on_click=lambda: st.session_state.update(copy_text=st.session_state.get("edit_hashtags", "")))

        if st.session_state.get("copy_text"):
            st.caption("The selected text is prepared below. Use the Copy button in your browser or select and copy the text.")
            st.code(st.session_state["copy_text"], language=None)
            st.session_state.copy_text = ""

        edited_title = st.session_state.get("edit_product_title", pack.product_title)
        edited_description = st.session_state.get("edit_product_description", pack.product_description)
        edited_instagram = st.session_state.get("edit_instagram", pack.instagram_caption)
        edited_whatsapp = st.session_state.get("edit_whatsapp", pack.whatsapp_message)
        edited_hashtags = st.session_state.get("edit_hashtags", " ".join(pack.hashtags))
        export_text = (
            f"# {edited_title}\n\n## Product description\n{edited_description}\n\n"
            f"## Instagram caption\n{edited_instagram}\n\n## WhatsApp message\n{edited_whatsapp}\n\n"
            f"## Hashtags\n{edited_hashtags}\n\n## Review notes\n"
            + ("\n".join(f"- {note}" for note in pack.review_notes) if pack.review_notes else "None")
        )
        st.download_button("Download full content pack (.md)", data=export_text, file_name="shopscribe-content-pack.md", mime="text/markdown")

        saved_mrp = st.session_state.get("last_mrp")
        saved_selling_price = st.session_state.get("last_selling_price")
        if saved_mrp is not None and saved_selling_price is not None:
            discount = calculate_discount_percent(saved_mrp, saved_selling_price)
            st.caption(f"Price check: ₹{saved_selling_price:,.2f} selling price vs ₹{saved_mrp:,.2f} MRP — {discount:.1f}% discount, calculated by Python.")
    except Exception as exc:
        st.error(f"Could not display the saved content pack: {exc}")

st.divider()
if DISABLE_SERVER_HISTORY:
    st.subheader("3. Generation history")
    st.caption(
        "History is disabled in the hosted demo so visitors cannot see a shared list of other users' products. "
        "Run ShopScribe AI locally to keep history in a SQLite database on your own computer."
    )
else:
    st.subheader("3. Local generation history")
    try:
        rows = get_recent_history(limit=5)
        if not rows:
            st.caption("No generated content packs saved yet.")
        else:
            for row in rows:
                with st.expander(f"{row['created_at']} · {row['product_name']} · {row['language']} · {row['model']}"):
                    st.code(row["content_json"], language="json")
    except Exception as exc:
        st.warning(f"Could not load local history: {exc}")

st.caption("ShopScribe AI is a prototype. Always verify product claims, ingredients, certifications, prices, and promotions against the original source before publishing.")
