from __future__ import annotations

from html import escape
from pathlib import Path

import gradio as gr


ALLOWED_DOCUMENT_TYPES = [".pdf", ".docx", ".txt"]

CSS = """
:root {
  --ink: #1b2a40;
  --muted: #68758a;
  --border: #e4e9f1;
  --green: #167e69;
}
html, body, .gradio-container {
  margin: 0 !important;
  padding: 0 !important;
  max-width: none !important;
  background: #f5f7fb !important;
  color: var(--ink);
  font-family: Inter, Arial, sans-serif;
}
.main, .contain {
  width: 100% !important;
  max-width: none !important;
  margin: 0 !important;
  padding: 0 !important;
}
footer, header { display: none !important; }
.app-shell { gap: 0 !important; align-items: stretch !important; min-height: 100vh; }
.sidebar {
  position: sticky;
  top: 0;
  align-self: flex-start;
  box-sizing: border-box;
  flex: 0 0 238px !important;
  width: 238px !important;
  min-width: 238px !important;
  height: 100vh;
  min-height: 100vh;
  padding: 25px 13px 20px;
  background: #101b31;
  color: #fff;
}
.brand { display: flex; align-items: center; gap: 12px; padding: 0 9px 45px; }
.brand-mark {
  display: grid; place-items: center; width: 38px; height: 38px; border-radius: 11px;
  background: #43c7a2; color: #102034; font-size: 23px; font-weight: 700;
}
.brand-name { font-size: 16px; font-weight: 700; }
.brand-name, .brand-subtitle, .profile-name, .profile-role { color: #fff; }
.brand-subtitle, .profile-role { color: #91a0b8; }
.brand-subtitle { margin-top: 3px; color: #91a0b8; font-size: 9px; letter-spacing: .6px; }
.nav-caption { padding: 0 11px 12px; color: #7887a0; font-size: 10px; font-weight: 700; letter-spacing: 1.4px; }
.nav-item {
  display: block; margin: 0 0 7px; padding: 12px 14px; border-radius: 8px;
  color: #aeb9ca; font-size: 13px; text-decoration: none;
}
.nav-item.active { background: #22314b; color: #fff; font-weight: 600; }
.sidebar .nav-label { color: inherit; }
.sidebar .nav-item:not(.active) { color: #aeb9ca; }
.nav-item.active > span:first-child { padding-right: 10px; color: #54d1ad; font-size: 17px; }
.nav-item.active .nav-label { color: #fff; font-size: 13px; white-space: nowrap; }
.profile {
  position: absolute; bottom: 20px; left: 23px; display: flex; align-items: center; gap: 12px;
}
.avatar {
  display: grid; place-items: center; width: 34px; height: 34px; border-radius: 50%;
  background: #334768; color: #fff; font-size: 11px; font-weight: 700;
}
.profile-name { color: #fff; font-size: 12px; font-weight: 600; }
.profile-role { margin-top: 3px; color: #91a0b8; font-size: 10px; }
.main-panel { min-width: 0 !important; padding: 25px 3.5vw 36px !important; gap: 8px !important; }
.main-panel .html-container { padding: 0 !important; }
.page-top { display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.breadcrumbs { color: #718096; font-size: 12px; }
.policy-pill {
  display: flex; align-items: center; gap: 9px; padding: 10px 14px; border: 1px solid #dce3ed;
  border-radius: 8px; background: #fff; color: #40516a; font-size: 12px; white-space: nowrap;
}
.policy-dot { width: 9px; height: 9px; border-radius: 50%; background: #2bb88a; }
.page-title { margin: 0 0 5px; color: #16243b; font-size: 28px; line-height: 1.25; font-weight: 700; }
.page-subtitle { margin: 0 0 15px; color: #68758a; font-size: 13px; }
.section-card {
  margin: 0 0 18px !important; padding: 22px 24px !important; border: 1px solid var(--border);
  border-radius: 12px !important; background: #fff; box-shadow: 0 5px 16px #1018280d;
  gap: 8px !important;
}
.section-card .html-container, .doc-panel .html-container, .run-row .html-container,
.run-row .prose, .assessment-header .html-container { padding: 0 !important; }
.section-heading { display: flex; align-items: center; gap: 11px; margin-bottom: 20px; }
.step-number {
  display: grid; place-items: center; width: 26px; height: 26px; border-radius: 50%;
  background: #e5f8f2; color: #18876d; font-size: 12px; font-weight: 700;
}
.section-title { color: #1b2a40; font-size: 15px; font-weight: 700; }
.section-description { margin: -13px 0 17px 37px; color: #7c8899; font-size: 11px; }
.field-label { margin: 0 0 6px; color: #68758a; font-size: 11px; font-weight: 600; }
.field-input input, .field-input textarea {
  min-height: 42px !important; height: 42px !important; border-color: #d9e0e9 !important;
  border-radius: 7px !important; color: #23334a !important; font-size: 13px !important;
  box-shadow: none !important;
}
.doc-panel {
  min-width: 0; padding: 12px 14px; border: 1px solid #d9e0e9; border-radius: 9px;
  background: #fbfcfe; gap: 7px !important;
}
.doc-title { margin-bottom: 5px; color: #26364c; font-size: 12px; font-weight: 700; }
.doc-hint { margin-bottom: 12px; color: #818da0; font-size: 10px; }
.upload-control { min-width: 0; margin-bottom: 0 !important; }
.upload-control button {
  min-height: 34px !important; padding: 0 12px !important; border: 1px solid #d9e0e9 !important;
  border-radius: 6px !important; background: #fff !important; color: #257cbd !important;
  font-size: 11px !important; box-shadow: none !important;
}
.doc-upload-row { align-items: center !important; gap: 8px !important; }
.doc-upload-row .upload-control { flex: 0 0 auto !important; width: auto !important; }
.doc-upload-row .upload-control button { width: auto !important; }
.file-list { display: flex; flex: 1; flex-wrap: wrap; gap: 7px; min-height: 27px; }
.file-chip {
  display: inline-flex; align-items: center; padding: 6px 9px; border: 1px solid #e2e7ef;
  border-radius: 5px; background: #fff; color: #46566d; font-size: 10px;
}
.file-empty { padding-top: 7px; color: #9aa4b2; font-size: 10px; }
.file-status { margin-top: 8px; color: #66758b; font-size: 10px; }
.run-row {
  align-items: center !important; margin: 0 0 28px !important; padding: 11px 15px;
  border: 1px solid #ccebe1; border-radius: 10px; background: #eaf7f3;
}
.ready-title { margin-bottom: 3px; color: #245d4d; font-size: 12px; font-weight: 700; }
.ready-copy { color: #638073; font-size: 10px; }
.primary-button button {
  min-height: 38px; border: 0 !important; border-radius: 7px !important;
  background: var(--green) !important; color: #fff !important; font-size: 12px !important;
  font-weight: 700 !important;
}
.assessment-header { align-items: center !important; justify-content: space-between !important; margin-bottom: 13px; }
.assessment-title { margin: 0; color: #1b2a40; font-size: 18px; font-weight: 700; }
.draft-pill {
  padding: 9px 14px; border-radius: 17px; background: #fff4dd; color: #8a5a08;
  font-size: 10px; font-weight: 700; letter-spacing: .2px;
}
.notice { margin-bottom: 14px; padding: 12px 14px; border: 1px solid #f1dfb8; border-radius: 8px; background: #fffaf0; color: #795b22; font-size: 12px; }
.empty-state {
  padding: 32px 20px !important; border: 1px dashed #d6deea; border-radius: 11px;
  background: #fff; color: #718096; text-align: center;
}
.empty-title { margin-bottom: 7px; color: #33445b; font-size: 13px; font-weight: 700; }
.empty-copy { font-size: 11px; line-height: 1.6; }
.footer-actions { align-items: center !important; justify-content: space-between !important; margin-top: 22px; }
.footer-actions button { min-height: 36px; border-radius: 7px !important; font-size: 11px !important; }
.footer-note { color: #77859a; font-size: 10px; }
.feedback { margin-top: 8px; color: #53647b; font-size: 12px; }
@media (max-width: 850px) {
  .sidebar { flex-basis: 68px !important; width: 68px !important; min-width: 68px !important; padding: 20px 8px; }
  .brand { justify-content: center; padding: 0 0 35px; }
  .brand-copy, .nav-caption, .nav-item:not(.active), .nav-item.active .nav-label, .profile-copy { display: none; }
  .nav-item.active { padding: 12px; text-align: center; }
  .nav-item.active > span:first-child { padding: 0; }
  .profile { left: 17px; }
  .main-panel { padding-right: 20px !important; padding-left: 20px !important; }
}
@media (max-width: 600px) {
  .main-panel { padding: 20px 13px 28px !important; }
  .page-top { align-items: flex-start; flex-direction: column; gap: 12px; }
  .page-title { font-size: 23px; }
  .section-card { padding: 17px 14px !important; }
  .run-row { align-items: stretch !important; }
  .assessment-header { align-items: flex-start !important; flex-direction: column; gap: 9px; }
}
"""


def _file_count(files: list[str] | str | None) -> int:
    if not files:
        return 0
    return len(files) if isinstance(files, list) else 1


def _file_list_html(files: list[str] | str | None) -> str:
    if not files:
        return '<div class="file-list"><span class="file-empty">No files selected</span></div>'
    paths = files if isinstance(files, list) else [files]
    chips = "".join(
        f'<span class="file-chip">&#128196; {escape(Path(path).name)}</span>'
        for path in paths
    )
    return f'<div class="file-list">{chips}</div>'


def document_status(
    policy_files: list[str] | str | None,
    evidence_files: list[str] | str | None,
) -> tuple[str, str, str]:
    policy_count = _file_count(policy_files)
    evidence_count = _file_count(evidence_files)
    total = policy_count + evidence_count
    if total == 0:
        summary = "Upload policy and vendor documents to prepare an assessment."
    else:
        summary = (
            f"{total} document{'s' if total != 1 else ''} uploaded "
            f"({policy_count} polic{'ies' if policy_count != 1 else 'y'}, "
            f"{evidence_count} evidence). Not indexed."
        )
    return (
        '<div class="ready-title">Assessment inputs</div>'
        f'<div class="ready-copy">{escape(summary)}</div>',
        _file_list_html(policy_files),
        _file_list_html(evidence_files),
    )


def run_assessment(
    vendor_name: str,
    intended_use: str,
    policy_files: list[str] | str | None,
    evidence_files: list[str] | str | None,
) -> str:
    missing = []
    if not (vendor_name or "").strip():
        missing.append("vendor name")
    if not (intended_use or "").strip():
        missing.append("intended use")
    if not _file_count(policy_files):
        missing.append("company policy document")
    if not _file_count(evidence_files):
        missing.append("vendor evidence document")

    if missing:
        return "Complete these items before assessing: " + ", ".join(missing) + "."

    return (
        "Your details and documents are ready. The assessment service is not configured yet, "
        "so no AI findings were generated."
    )


with gr.Blocks(title="AI Vendor Risk Assessor") as demo:
    with gr.Row(elem_classes="app-shell"):
        with gr.Column(elem_classes="sidebar", scale=0):
            gr.HTML(
                """
                <div class="brand">
                  <div class="brand-mark">✓</div>
                  <div class="brand-copy">
                    <div class="brand-name">VendorRisk</div>
                    <div class="brand-subtitle">ASSESSMENT WORKSPACE</div>
                  </div>
                </div>
                <div class="nav-caption">WORKSPACE</div>
                <a class="nav-item active" href="#"><span>＋</span><span class="nav-label">New assessment</span></a>
                <a class="nav-item" href="#"><span class="nav-label">Assessments</span></a>
                <a class="nav-item" href="#"><span class="nav-label">Policy library</span></a>
                <a class="nav-item" href="#"><span class="nav-label">Settings</span></a>
                <div class="profile">
                  <div class="avatar">JD</div>
                  <div class="profile-copy">
                    <div class="profile-name">Jordan Davis</div>
                    <div class="profile-role">Security analyst</div>
                  </div>
                </div>
                """
            )

        with gr.Column(elem_classes="main-panel", scale=1):
            with gr.Row(elem_classes="page-top"):
                gr.HTML('<div class="breadcrumbs">Assessments&nbsp; / &nbsp;New assessment</div>')
                gr.HTML(
                    '<div class="policy-pill"><span class="policy-dot"></span>'
                    "Policy set: Core v1.0</div>"
                )
            gr.HTML(
                '<h1 class="page-title">AI Vendor Risk Assessor</h1>'
                '<p class="page-subtitle">Review vendor evidence against your company policies.</p>'
            )

            with gr.Column(elem_classes="section-card"):
                gr.HTML(
                    '<div class="section-heading"><span class="step-number">1</span>'
                    '<span class="section-title">Vendor details</span></div>'
                )
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.HTML('<div class="field-label">VENDOR NAME</div>')
                        vendor_name = gr.Textbox(
                            show_label=False,
                            placeholder="Enter vendor name",
                            elem_classes="field-input",
                        )
                    with gr.Column(scale=1):
                        gr.HTML('<div class="field-label">INTENDED USE</div>')
                        intended_use = gr.Textbox(
                            show_label=False,
                            placeholder="Describe how your organization will use this vendor",
                            elem_classes="field-input",
                        )

            with gr.Column(elem_classes="section-card"):
                gr.HTML(
                    '<div class="section-heading"><span class="step-number">2</span>'
                    '<span class="section-title">Documents</span></div>'
                    '<div class="section-description">Upload company requirements and vendor evidence to begin.</div>'
                )
                with gr.Row():
                    with gr.Column(elem_classes="doc-panel", scale=1):
                        gr.HTML('<div class="doc-title">Company policies</div>')
                        gr.HTML(
                            '<div class="doc-hint">Internal requirements used as the assessment checklist</div>'
                        )
                        with gr.Row(elem_classes="doc-upload-row"):
                            policy_list = gr.HTML(
                                '<div class="file-list"><span class="file-empty">No files selected</span></div>'
                            )
                            policy_files = gr.UploadButton(
                                "＋ Add files",
                                file_count="multiple",
                                file_types=ALLOWED_DOCUMENT_TYPES,
                                type="filepath",
                                elem_classes="upload-control",
                            )
                    with gr.Column(elem_classes="doc-panel", scale=1):
                        gr.HTML('<div class="doc-title">Vendor evidence</div>')
                        gr.HTML(
                            '<div class="doc-hint">Questionnaires, reports, agreements, and other evidence</div>'
                        )
                        with gr.Row(elem_classes="doc-upload-row"):
                            evidence_list = gr.HTML(
                                '<div class="file-list"><span class="file-empty">No files selected</span></div>'
                            )
                            evidence_files = gr.UploadButton(
                                "＋ Add files",
                                file_count="multiple",
                                file_types=ALLOWED_DOCUMENT_TYPES,
                                type="filepath",
                                elem_classes="upload-control",
                            )

            with gr.Row(elem_classes="run-row"):
                with gr.Column(scale=1):
                    document_summary = gr.HTML(
                        '<div class="ready-title">Assessment inputs</div>'
                        '<div class="ready-copy">Upload policy and vendor documents to prepare an assessment.</div>'
                    )
                with gr.Column(scale=0, min_width=170, elem_classes="primary-button"):
                    run_button = gr.Button("Run assessment  →", variant="primary")

            assessment_feedback = gr.Markdown("", elem_classes="feedback")
            upload_outputs = [document_summary, policy_list, evidence_list]
            policy_files.upload(
                fn=document_status,
                inputs=[policy_files, evidence_files],
                outputs=upload_outputs,
            )
            evidence_files.upload(
                fn=document_status,
                inputs=[policy_files, evidence_files],
                outputs=upload_outputs,
            )
            run_button.click(
                fn=run_assessment,
                inputs=[vendor_name, intended_use, policy_files, evidence_files],
                outputs=assessment_feedback,
            )

            with gr.Row(elem_classes="assessment-header"):
                gr.HTML('<h2 class="assessment-title">Assessment findings</h2>')
                gr.HTML('<div class="draft-pill">DRAFT · AWAITING HUMAN REVIEW</div>')
            gr.HTML(
                '<div class="notice">The assessment service is not connected yet. '
                "Uploaded files are not indexed or analyzed.</div>"
                '<div class="empty-state">'
                '<div class="empty-title">No findings yet</div>'
                '<div class="empty-copy">Run an assessment after the analysis service is configured. '
                "Findings will appear here for human review.</div></div>"
            )

            with gr.Row(elem_classes="footer-actions"):
                gr.Button("Save draft", interactive=False)
                gr.HTML('<div class="footer-note">Review and finalization become available after assessment.</div>')
                gr.Button("Finalize assessment", variant="primary", interactive=False)


if __name__ == "__main__":
    demo.launch(css=CSS)