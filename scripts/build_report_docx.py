from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "Lokoja_Traffic_Congestion_Project_Report.docx"
METADATA_PATH = PROJECT_ROOT / "artifacts" / "training_metadata.json"
SCREENSHOT_DIR = PROJECT_ROOT / "artifacts" / "report_screenshots"


def set_run_font(run, size=12, bold=False, italic=False):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    set_run_font(run, size=11)

    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")

    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "

    fld_separate = OxmlElement("w:fldChar")
    fld_separate.set(qn("w:fldCharType"), "separate")

    text = OxmlElement("w:t")
    text.text = "1"

    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")

    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_separate)
    run._r.append(text)
    run._r.append(fld_end)


def configure_document(doc: Document):
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1.2)
    section.right_margin = Inches(1.0)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    style._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    style.font.size = Pt(12)

    paragraph_format = style.paragraph_format
    paragraph_format.line_spacing = 2
    paragraph_format.space_after = Pt(0)
    paragraph_format.space_before = Pt(0)

    footer = section.footer
    footer_p = footer.paragraphs[0]
    add_page_number(footer_p)


def add_paragraph(doc: Document, text: str, bold_prefix: str | None = None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Inches(0.5)
    p.paragraph_format.line_spacing = 2
    p.paragraph_format.space_after = Pt(0)
    if bold_prefix and text.startswith(bold_prefix):
        prefix = p.add_run(bold_prefix)
        set_run_font(prefix, bold=True)
        rest = p.add_run(text[len(bold_prefix):])
        set_run_font(rest)
        return p
    run = p.add_run(text)
    set_run_font(run)
    return p


def add_heading(doc: Document, text: str, level: int = 1):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.line_spacing = 2
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(0)
    style_map = {1: 14, 2: 12}
    run = p.add_run(text)
    set_run_font(run, size=style_map.get(level, 12), bold=True)
    return p


def add_center_block(doc: Document, lines: list[str], bold_first: bool = False):
    for index, line in enumerate(lines):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing = 2
        run = p.add_run(line)
        set_run_font(run, size=12, bold=bold_first and index == 0)


def add_numbered_objectives(doc: Document, objectives: list[str]):
    for item in objectives:
        p = doc.add_paragraph(style="List Number")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 2
        run = p.add_run(item)
        set_run_font(run)


def page_break(doc: Document):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def add_figure(doc: Document, image_path: Path, caption: str, width_inches: float = 5.8):
    if not image_path.exists():
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(image_path), width=Inches(width_inches))
    caption_p = doc.add_paragraph()
    caption_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_run = caption_p.add_run(caption)
    set_run_font(caption_run, size=11, italic=True)


def add_table(doc: Document, headers: list[str], rows: list[list[str]], column_widths: list[float] | None = None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = False

    header_cells = table.rows[0].cells
    for index, header in enumerate(headers):
        cell = header_cells[index]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(header)
        set_run_font(run, size=11, bold=True)
        if column_widths:
            cell.width = Inches(column_widths[index])

    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            cells[index].text = ""
            p = cells[index].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(str(value))
            set_run_font(run, size=10)
            if column_widths:
                cells[index].width = Inches(column_widths[index])

    doc.add_paragraph()
    return table


def load_training_metadata() -> dict:
    if not METADATA_PATH.exists():
        return {}
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))


def build_document():
    doc = Document()
    configure_document(doc)
    metadata = load_training_metadata()
    interpretation = metadata.get("interpretation", {})
    feature_importance = metadata.get("feature_importance", [])
    lime_summary = interpretation.get("lime", {}).get("summary", [])
    shap_summary = interpretation.get("shap", {}).get("summary", [])
    pdp_summary = interpretation.get("pdp", {}).get("summary", [])
    fi_plot = Path(interpretation.get("feature_importance", {}).get("plot", "")) if interpretation.get("feature_importance", {}).get("plot") else None
    pdp_plot = None
    pdp_plots = interpretation.get("pdp", {}).get("plots", [])
    if pdp_plots:
        pdp_plot = Path(pdp_plots[0])
    lime_plot = Path(interpretation.get("lime", {}).get("plot", "")) if interpretation.get("lime", {}).get("plot") else None
    shap_plot = Path(interpretation.get("shap", {}).get("plot", "")) if interpretation.get("shap", {}).get("plot") else None
    dataset_profile = metadata.get("dataset_profile", {})
    categorical_options = dataset_profile.get("categorical_options", {})
    numeric_ranges = dataset_profile.get("numeric_ranges", {})
    congestion_thresholds = metadata.get("congestion_thresholds", {})
    peak_hours = metadata.get("peak_hours", [])
    hourly_trends = metadata.get("hourly_trends", [])
    location_patterns = metadata.get("location_patterns", [])
    dashboard_screenshot = SCREENSHOT_DIR / "dashboard_overview.png"
    prediction_screenshot = SCREENSHOT_DIR / "prediction_output.png"
    comparison_screenshot = SCREENSHOT_DIR / "comparison_state.png"
    analytics_screenshot = SCREENSHOT_DIR / "analytics_section.png"

    high_total = sum(item.get("High", 0) for item in hourly_trends)
    medium_total = sum(item.get("Medium", 0) for item in hourly_trends)
    low_total = sum(item.get("Low", 0) for item in hourly_trends)
    top_locations = sorted(location_patterns, key=lambda item: item.get("High", 0), reverse=True)[:3]
    top_hours = sorted(hourly_trends, key=lambda item: item.get("High", 0), reverse=True)[:5]

    add_center_block(
        doc,
        [
            "TRAFFIC CONGESTION PREDICTION AND DECISION SUPPORT SYSTEM FOR LOKOJA",
            "",
            "An Undergraduate Project Report",
            "Submitted in Partial Fulfilment of the Requirements for the Award of the Degree of",
            "Bachelor of Science in Computer Science",
            "",
            "[Department Name]",
            "[Faculty Name]",
            "[Institution Name]",
            "",
            "By",
            "[Student Full Name]",
            "[Matriculation Number]",
            "",
            "April 2026",
        ],
        bold_first=True,
    )

    page_break(doc)

    add_heading(doc, "CERTIFICATION")
    add_paragraph(
        doc,
        "This is to certify that this project report titled 'Traffic Congestion Prediction and Decision Support System for Lokoja' was carried out by [Student Full Name] of [Matriculation Number] in the Department of [Department Name], [Institution Name], under the supervision of [Supervisor Name].",
    )
    add_paragraph(doc, "______________________________        ______________________________")
    add_paragraph(doc, "Supervisor's Signature/Date                 Head of Department/Date")

    page_break(doc)

    add_heading(doc, "DEDICATION")
    add_paragraph(
        doc,
        "This work is dedicated to God Almighty, my family, and everyone whose efforts contribute to safer and more efficient transportation systems in Lokoja and beyond.",
    )

    page_break(doc)

    add_heading(doc, "ACKNOWLEDGEMENTS")
    add_paragraph(
        doc,
        "I sincerely appreciate God Almighty for the strength and wisdom to complete this project. I also thank my supervisor, lecturers, family, and friends for their guidance, encouragement, and support throughout the study. Special appreciation goes to all individuals and institutions whose insights, feedback, and academic resources contributed to the successful development of this work.",
    )

    page_break(doc)

    add_heading(doc, "ABSTRACT")
    add_paragraph(
        doc,
        "Urban traffic congestion affects travel time, economic productivity, and commuter safety in Lokoja. This project presents a traffic congestion prediction and decision support system designed to estimate future traffic conditions from contextual variables such as hour of day, day of week, location, weather, road condition, road type, vehicle mix, and proximity to commercial hubs. Following supervisory guidance, the machine learning task was formulated as a regression problem in which traffic volume is predicted directly, after which predicted values are mapped into Low, Medium, and High congestion bands using dataset-derived thresholds. The system combines a React-based user interface, a Spring Boot backend API layer, and a Python machine learning service. Experimental results from the current implementation show that the selected Random Forest Regressor achieves strong predictive performance on the working synthetic dataset, with an R-squared value of 0.893. Model interpretation is supported through feature importance analysis, threshold-based congestion translation, and explanation statements that connect predicted outcomes to temporal and contextual conditions. Because the present dataset is synthetic, the results should be understood primarily as proof of concept evidence for system feasibility rather than final proof of real-world deployment readiness. The project demonstrates that a modular intelligent traffic support system can provide useful transport insights for Lokoja without requiring full route navigation capabilities.",
    )

    page_break(doc)

    add_heading(doc, "TABLE OF CONTENTS")
    add_paragraph(doc, "The table of contents will be updated automatically as the report is revised in Microsoft Word.")
    add_heading(doc, "LIST OF FIGURES")
    add_paragraph(doc, "Figure 1: System architecture of the Lokoja traffic decision support platform.")
    add_paragraph(doc, "Figure 2: Permutation feature importance for the selected regression model.")
    add_paragraph(doc, "Figure 3: Partial dependence plots showing average marginal feature effects.")
    add_paragraph(doc, "Figure 4: LIME local explanation for a sample regression prediction.")
    add_paragraph(doc, "Figure 5: SHAP summary chart using mean absolute contribution values.")
    add_paragraph(doc, "Figure 6: Responsive frontend dashboard overview of the Lokoja traffic decision support interface.")
    add_paragraph(doc, "Figure 7: Prediction output view showing the regression result and derived congestion band.")
    add_paragraph(doc, "Figure 8: Scenario comparison view showing what-if simulation results.")
    add_paragraph(doc, "Figure 9: Analytics section of the frontend showing model insight visualization.")
    add_heading(doc, "LIST OF TABLES")
    add_paragraph(doc, "Table 1: Dataset feature summary.")
    add_paragraph(doc, "Table 2: Software modules and implementation responsibilities.")
    add_paragraph(doc, "Table 3: Regression performance comparison.")
    add_paragraph(doc, "Table 4: Congestion thresholds derived from predicted traffic volume.")
    add_paragraph(doc, "Table 5: Integration and validation test summary.")
    add_heading(doc, "LIST OF ABBREVIATIONS")
    add_paragraph(doc, "API - Application Programming Interface")
    add_paragraph(doc, "ML - Machine Learning")
    add_paragraph(doc, "RMSE - Root Mean Squared Error")
    add_paragraph(doc, "MAE - Mean Absolute Error")
    add_paragraph(doc, "UI - User Interface")

    page_break(doc)

    add_heading(doc, "CHAPTER ONE: INTRODUCTION")
    add_heading(doc, "1.1 Background of the Study", level=2)
    add_paragraph(
        doc,
        "Traffic congestion has become a persistent problem in many developing urban centres due to increasing population growth, commercial activities, road usage intensity, and limited infrastructure expansion. Lokoja, as a major junction city and administrative centre, experiences daily traffic pressure across locations such as Lokoja Central/Old Market, Ganaja, Kabba Junction, Nataco, and Felele. Congestion at these points affects commuting efficiency, business operations, fuel consumption, and emergency mobility. With advances in machine learning, traffic patterns can now be studied from historical or simulated transport data to support anticipatory decision-making. This project therefore focuses on building a decision support system that predicts traffic conditions for Lokoja and helps users understand likely congestion outcomes before commencing travel.",
    )
    add_heading(doc, "1.2 Problem Statement", level=2)
    add_paragraph(
        doc,
        "Road users in Lokoja often make travel decisions without reliable evidence about expected congestion conditions. Existing informal judgment methods depend heavily on personal experience, which can be inconsistent and inaccurate, especially during weather changes, commercial activity surges, or peak travel periods. In addition, many intelligent transport solutions emphasize route navigation, whereas a smaller but important need is decision support: informing commuters, planners, and administrators about likely traffic intensity and the factors driving it. There is therefore a need for a localized, data-driven system that can estimate traffic conditions in Lokoja and present the results in a form that is understandable and actionable.",
    )
    add_heading(doc, "1.3 Aim and Objectives", level=2)
    add_paragraph(
        doc,
        "The aim of this study is to develop a traffic congestion prediction and decision support system for Lokoja using machine learning and a modular web-based architecture.",
    )
    add_numbered_objectives(
        doc,
        [
            "To identify and prepare relevant traffic-related features from the Lokoja traffic dataset.",
            "To develop a preprocessing and machine learning pipeline that predicts traffic volume as a regression target.",
            "To classify predicted traffic volume into Low, Medium, and High congestion bands using dataset-derived thresholds.",
            "To design an API-ready machine learning service that supports prediction, retraining, and insight generation.",
            "To provide explanatory outputs and scenario-based simulation that improve user decision-making.",
        ],
    )
    add_heading(doc, "1.4 Significance of the Study", level=2)
    add_paragraph(
        doc,
        "This study is significant because it demonstrates how data-driven methods can support transport awareness and planning in Lokoja. Commuters can use the system to decide when and where to travel, while researchers and administrators can use it as a basis for future smart mobility studies. The project also contributes academically by showing how a locally scoped machine learning system can be framed as a practical decision support tool rather than a full navigation platform.",
    )
    add_paragraph(
        doc,
        "From a methodological perspective, the project is significant because it applies a more defensible machine learning formulation than many student traffic studies. Instead of directly predicting coarse congestion labels from the outset, the system predicts traffic volume as a continuous quantity and then derives congestion classes through transparent thresholds. This gives the report a stronger analytical chain, since the qualitative labels shown to users are backed by a quantitative model output.",
    )
    add_paragraph(
        doc,
        "The project is also significant in terms of explainable artificial intelligence. Many prediction systems produce outputs without showing the reasoning patterns behind them, which reduces trust and makes academic evaluation difficult. By integrating feature importance, partial dependence analysis, LIME, and SHAP, this study moves beyond raw prediction and provides an interpretable account of how the model behaves. This is particularly valuable in an undergraduate project because it demonstrates not only implementation ability, but also analytical understanding.",
    )
    add_heading(doc, "1.5 Scope of the Study", level=2)
    add_paragraph(
        doc,
        "The study covers the development of a traffic prediction system based on the provided Lokoja dataset. Inputs considered include hour, day of week, weekend indicator, location, road type, weather, road condition, vehicle mix, and proximity to commercial hubs. The system predicts traffic volume and then interprets the result into congestion categories. The project includes model development, API design, explanation logic, dashboard-oriented outputs, and a structure for future frontend and backend integration. Real-time GPS tracking, route optimization, and live map navigation are outside the scope of this work.",
    )
    add_heading(doc, "1.6 Limitations of the Study", level=2)
    add_paragraph(
        doc,
        "The study is limited by the available dataset size, the absence of live streaming traffic data, and the dependence on patterns captured in the current dataset. A major limitation is that the present dataset is synthetic rather than collected from direct field observation in Lokoja. This means the learned relationships are useful for prototyping, architecture validation, and algorithm testing, but they cannot yet be treated as definitive evidence of real-world traffic behaviour. The generated congestion classes are also threshold-based summaries of predicted traffic volume, which means they depend on the quality and representativeness of the available data. Time and resource limitations further restrict large-scale field validation during the current phase of the project.",
    )
    add_heading(doc, "1.7 Definition of Terms", level=2)
    add_paragraph(doc, "Traffic Volume refers to the estimated quantity of vehicle flow on a road segment within a given context.")
    add_paragraph(doc, "Congestion Level refers to the interpreted traffic condition band derived from predicted traffic volume.")
    add_paragraph(doc, "Decision Support System refers to a software system that assists users in making informed choices from analyzed data.")
    add_paragraph(doc, "Regression Model refers to a machine learning model that predicts continuous numerical values.")
    add_heading(doc, "1.8 Research Questions", level=2)
    add_paragraph(
        doc,
        "The study is guided by the following questions: how can contextual variables such as hour, day, location, weather, road condition, and vehicle mix be used to predict traffic volume in Lokoja; how can the predicted traffic volume be translated into understandable congestion bands for users; and how can model-interpretation techniques be used to explain the resulting traffic predictions in a transparent and academically meaningful way?",
    )

    page_break(doc)

    add_heading(doc, "CHAPTER TWO: LITERATURE REVIEW")
    add_heading(doc, "2.1 Introduction", level=2)
    add_paragraph(
        doc,
        "This chapter reviews the concepts, theories, and prior empirical studies relevant to traffic prediction and decision support systems. The current draft provides a structured base that will be expanded with cited literature from journals, conference proceedings, and textbooks during the full literature review stage.",
    )
    add_heading(doc, "2.2 Conceptual Review", level=2)
    add_paragraph(
        doc,
        "Key concepts in this project include traffic congestion, traffic volume estimation, predictive analytics, machine learning for transport systems, explainable prediction, and decision support. Traffic congestion may be viewed as the operational effect of high traffic density relative to available road capacity. In this project, congestion is operationalized indirectly: the system predicts traffic volume first and then maps the predicted value into qualitative bands that users can interpret quickly.",
    )
    add_heading(doc, "2.3 Theoretical Framework", level=2)
    add_paragraph(
        doc,
        "The theoretical basis of the study is rooted in predictive analytics and decision support theory. Predictive analytics emphasizes the use of historical patterns to estimate future outcomes, while decision support theory focuses on delivering analyzed information that improves human judgment. Together, these perspectives justify a system that does not merely store traffic data but transforms it into predictive insights and explanatory guidance.",
    )
    add_heading(doc, "2.4 Empirical Review", level=2)
    add_paragraph(
        doc,
        "Empirical studies in the traffic prediction domain commonly apply statistical models, support vector methods, neural networks, and ensemble tree methods to estimate road conditions, travel demand, or traffic flow. Many studies report that ensemble techniques perform well when nonlinear relationships exist among contextual variables such as time, weather, and location. The final report will compare such findings with the performance observed in this project's Lokoja dataset.",
    )
    add_heading(doc, "2.5 Gap Identification", level=2)
    add_paragraph(
        doc,
        "A notable gap in many existing implementations is the limited attention given to localized, interpretable, and academically manageable decision support tools for medium-sized Nigerian cities. Another gap is the overemphasis on navigation or route optimization, whereas many student projects and civic use cases require simpler predictive insight systems. This study addresses those gaps by focusing on Lokoja and by combining regression-based prediction with a readable congestion interpretation layer.",
    )
    add_heading(doc, "2.6 Summary of Literature Review", level=2)
    add_paragraph(
        doc,
        "The reviewed concepts and empirical directions support the relevance of a localized machine learning solution for traffic decision support. The literature chapter will later be strengthened with referenced sources, comparative summaries, and deeper discussion of algorithm suitability, explainability, and practical deployment constraints.",
    )

    page_break(doc)

    add_heading(doc, "CHAPTER THREE: METHODOLOGY")
    add_heading(doc, "3.1 Introduction", level=2)
    add_paragraph(
        doc,
        "This chapter describes the methodological approach used to develop the traffic congestion prediction and decision support system for Lokoja. It explains the research design, data source, model design, algorithm selection, evaluation strategy, and implementation tools.",
    )
    add_heading(doc, "3.2 Research Design", level=2)
    add_paragraph(
        doc,
        "The study adopts a design-and-implementation approach with experimental evaluation. The practical system is built as an integrated software solution consisting of a frontend user interface, a backend API layer, and a dedicated machine learning service. Model performance is evaluated quantitatively using standard regression metrics.",
    )
    add_heading(doc, "3.3 Data Source / Data Collection", level=2)
    add_paragraph(
        doc,
        "The project uses the dataset stored in traffic_pred_dataset_updated.csv. The dataset contains 1,000 records and includes contextual variables such as hour, day of week, weekend status, location, road type, weather, road condition, vehicle mix, and near-commercial-hub indicator. The `traffic_volume` column is used as the regression target, while the legacy `congestion_level` column is retained only as a contextual dataset field and not as the direct model target. It is important to note that this dataset is synthetic. As a result, the current phase of the study focuses on validating the system design, machine learning pipeline, and interpretation workflow rather than claiming final real-world traffic forecasting accuracy for Lokoja.",
    )
    add_heading(doc, "3.3.1 Exploratory Data Analysis", level=2)
    add_paragraph(
        doc,
        "Preliminary analysis of the dataset was carried out before model training in order to understand the structure and practical meaning of the variables. The data spans the full 24-hour daily cycle, all seven days of the week, eight named Lokoja zones, three road types, two weather states, three vehicle-mix categories, and binary indicators for weekend status and proximity to commercial hubs. This spread is useful because it allows the model to observe temporal, spatial, and environmental variation rather than learning from a narrow traffic context.",
    )
    add_paragraph(
        doc,
        "A notable property of the synthetic dataset is that the congestion classes represented in the legacy `congestion_level` field are almost perfectly balanced, with approximately 340 High cases, 330 Medium cases, and 330 Low cases. Although these classes are no longer used as the direct machine learning target, their balance is still analytically useful because it suggests that the synthetic data generation process was designed to avoid severe category skew. In practical terms, this means the corresponding traffic-volume distribution likely covers low, medium, and high traffic situations in a comparatively even way.",
    )
    add_paragraph(
        doc,
        "Temporal pattern analysis also reveals that congestion intensity is not evenly distributed across the day. The strongest High-congestion counts occur around hours 19, 18, 17, 7, and 16, indicating clear morning and especially late-afternoon to evening pressure in the simulated Lokoja mobility pattern. At the location level, Kabba Junction and Lokoja Central/Old Market produce some of the largest High-congestion counts, while areas such as Phase I and Zango show comparatively lighter severe-congestion presence. These observations are consistent with the intuition that commercial and junction-heavy areas accumulate more traffic than quieter residential zones.",
    )
    add_paragraph(
        doc,
        "The exploratory analysis also helped justify the regression formulation. The observed traffic-volume range extends from approximately 8.23 to 223.23, which provides a sufficiently broad continuous target for regression modeling. Instead of treating congestion bands as the primary target, the system now predicts this continuous volume value and then interprets it with threshold-based ranges. This approach preserves more information from the data and makes later analysis more defensible because qualitative labels are derived from an underlying quantitative estimate.",
    )
    add_table(
        doc,
        ["Feature", "Type", "Role / Meaning"],
        [
            ["hour", "Numeric", "Hour of day used to capture diurnal traffic rhythm."],
            ["day_of_week", "Numeric", "Day index used to model weekly variation."],
            ["is_weekend", "Binary", "Derived weekend flag used to distinguish weekday and weekend demand."],
            ["location", "Categorical", "Lokoja zone where the traffic context is being evaluated."],
            ["road_type", "Categorical", "Road environment such as Urban, Highway, or Residential."],
            ["weather", "Categorical", "Weather state affecting travel intensity and road movement."],
            ["road_condition", "Numeric", "Ordinal road-quality condition score."],
            ["vehicle_mix", "Categorical", "Dominant vehicle composition in the traffic context."],
            ["near_commercial_hub", "Binary", "Whether the segment is near a commercially active area."],
            ["traffic_volume", "Numeric Target", "Continuous variable predicted by the regression model."],
        ],
        [1.4, 1.2, 3.7],
    )
    add_paragraph(doc, "Table 1: Dataset feature summary.")
    add_heading(doc, "3.4 Population and Sample Size", level=2)
    add_paragraph(
        doc,
        "The effective population for the model development stage consists of all valid records available in the working dataset. The current sample size is 1,000 observations. During training, the data is split into training and testing subsets using an 80:20 proportion for model evaluation.",
    )
    add_heading(doc, "3.5 System Architecture / Model Design", level=2)
    add_paragraph(
        doc,
        "The logical architecture of the system follows a three-layer interaction model. The React frontend captures user inputs and displays predictions, explanations, and charts. The Spring Boot backend provides integration endpoints and acts as a coordinating service. The Python machine learning service performs preprocessing, training, prediction, and insight generation. Within the machine learning layer, predicted traffic volume is transformed into Low, Medium, and High congestion bands using learned dataset thresholds.",
    )
    add_heading(doc, "3.6 Methods / Algorithms Used", level=2)
    add_paragraph(
        doc,
        "A baseline Linear Regression model and a main Random Forest Regressor were implemented. Categorical features are encoded through one-hot encoding, while numerical features are imputed and scaled within a preprocessing pipeline. The final saved model is selected automatically based on the lower Root Mean Squared Error observed on the test set. At the current stage, the Random Forest Regressor is the preferred model.",
    )
    add_heading(doc, "3.6.1 Preprocessing Pipeline", level=2)
    add_paragraph(
        doc,
        "The preprocessing pipeline was designed to be API-ready and reusable during both training and prediction. Numerical features are validated against known ranges and prepared for model input, while categorical features are validated against known dataset options and encoded using one-hot transformation. Optional fields such as road_type, vehicle_mix, near_commercial_hub, and is_weekend are given dataset-informed defaults where necessary. This approach reduces the risk of mismatch between the training environment and live prediction requests.",
    )
    add_paragraph(
        doc,
        "An important design decision in the pipeline is the derivation of is_weekend from day_of_week when the value is not explicitly provided by the caller. This makes the input interface simpler while preserving the feature's analytical usefulness. The same service also normalizes request values before prediction, which ensures that the backend and future frontend can consume a consistent machine learning contract.",
    )
    add_heading(doc, "3.6.2 Threshold Derivation for Congestion Bands", level=2)
    add_paragraph(
        doc,
        "After the regression model predicts traffic volume, the value is interpreted using threshold bands learned from the dataset profile. This makes congestion classification a post-processing stage rather than the direct learning target. In the present system, values less than or equal to 56.23 are treated as Low congestion, values above 56.23 and up to 98.32 are treated as Medium congestion, and values above 98.32 are treated as High congestion. The thresholding layer is central to the system's decision-support role because it translates technical regression output into a user-friendly summary.",
    )
    add_heading(doc, "3.7 Evaluation Metrics", level=2)
    add_paragraph(
        doc,
        "Model performance is evaluated using Mean Absolute Error, Root Mean Squared Error, and the coefficient of determination (R-squared). These metrics are suitable for regression because they measure prediction error magnitude and the proportion of target variation explained by the model.",
    )
    add_heading(doc, "3.8 Tools and Technologies", level=2)
    add_paragraph(
        doc,
        "The frontend layer is planned with React and Tailwind CSS. The backend integration layer uses Java with Spring Boot. The machine learning service is implemented in Python using pandas and scikit-learn. Visualization is intended through Chart.js, while model artifacts are stored for reuse and retraining.",
    )
    add_heading(doc, "3.8.1 Validation Strategy", level=2)
    add_paragraph(
        doc,
        "Validation was carried out at multiple levels. At the model level, the baseline and main regressors were compared using the same train-test split and the same performance metrics. At the service level, prediction requests were tested directly against the Python API. At the integration level, the Spring Boot backend was verified through health checks, automated test execution, and end-to-end prediction flow against the running ML service. This multi-layer validation approach strengthens the credibility of the implementation because it checks not only model quality but also system behavior.",
    )
    add_heading(doc, "3.9 Ethical Considerations", level=2)
    add_paragraph(
        doc,
        "The project relies on a structured synthetic dataset and does not perform invasive personal tracking or route surveillance. Care is taken to use the model only for academic and decision support purposes, and the study avoids misleading users by clearly presenting congestion bands as interpretations of predicted traffic volume rather than guaranteed real-time facts. The synthetic nature of the dataset is disclosed because it affects how responsibly the system results should be interpreted and reported.",
    )

    page_break(doc)

    add_heading(doc, "CHAPTER FOUR: RESULTS AND DISCUSSION")
    add_heading(doc, "4.1 Introduction", level=2)
    add_paragraph(
        doc,
        "This chapter presents the current implementation state, training results, model interpretation findings, and analytical observations from the machine learning service developed for the project.",
    )
    add_heading(doc, "4.2 Implementation Overview", level=2)
    add_paragraph(
        doc,
        "At the present stage, the machine learning service has been structured as a reusable production-style module with dataset-aware validation, training, prediction, explanation, and insights endpoints. The input handling now reflects the true dataset schema and no longer requests traffic volume from the user, since traffic volume is the predicted target. Because the current dataset is synthetic, the implementation should be interpreted as a proof-of-concept platform that is ready for later validation with real observational traffic data.",
    )
    add_paragraph(
        doc,
        "The full system is organized as a modular three-tier platform. The React frontend is responsible for user input, scenario simulation, and visualization. The Spring Boot backend exposes stable application endpoints and handles integration concerns between the user-facing layer and the machine learning service. The Python service performs dataset-driven validation, preprocessing, model loading, training, insights generation, and prediction explanation. This separation of responsibilities improves maintainability and also makes the work easier to defend academically because each layer has a clearly defined role.",
    )
    arch = doc.add_paragraph()
    arch.alignment = WD_ALIGN_PARAGRAPH.CENTER
    arch.paragraph_format.line_spacing = 1.5
    for line in [
        "Frontend (React + Tailwind)",
        "        ↓",
        "Backend API (Spring Boot)",
        "        ↓",
        "ML Service (Python / scikit-learn)",
        "        ↓",
        "Model Artifacts + Dataset",
    ]:
        run = arch.add_run(line + "\n")
        set_run_font(run, size=11, bold=False)
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap_run = cap.add_run("Figure 1: System architecture of the Lokoja traffic decision support platform.")
    set_run_font(cap_run, size=11, italic=True)
    add_paragraph(
        doc,
        "Beyond the service modules, the frontend now presents the project as an actual decision-support dashboard rather than a raw prediction form. The final interface organizes the system into overview, prediction, analytics, and system-note sections, with compact section navigation on smaller screens and a persistent sidebar pattern on larger screens. This makes the application more appropriate for academic demonstration, repeated scenario testing, and supervisor review.",
    )
    add_figure(
        doc,
        dashboard_screenshot,
        "Figure 6: Responsive frontend dashboard overview of the Lokoja traffic decision support interface.",
        width_inches=5.9,
    )
    add_paragraph(
        doc,
        "Academically, Figure 6 demonstrates that the system satisfies the usability and integration objectives stated earlier in the report. The dashboard consolidates dataset-aware input controls, summary indicators, section navigation, and explanatory status messaging within a single coherent interface, showing that the proposed architecture has been translated into an operational decision-support environment rather than an isolated prediction script.",
    )
    add_table(
        doc,
        ["Module", "Primary Responsibility", "Current Status"],
        [
            ["React frontend", "Collect inputs, run what-if simulation, display prediction results and charts.", "Implemented"],
            ["Spring Boot backend", "Expose /api endpoints and relay requests to the ML service.", "Implemented"],
            ["Python ML service", "Train model, serve predictions, produce interpretation outputs.", "Implemented"],
            ["Artifacts layer", "Persist model files, thresholds, metrics, and interpretation plots.", "Implemented"],
        ],
        [1.8, 3.8, 1.3],
    )
    add_paragraph(doc, "Table 2: Software modules and implementation responsibilities.")
    add_heading(doc, "4.3 Results Presentation", level=2)
    add_paragraph(doc, "Current regression results are summarized as follows:")
    add_paragraph(doc, "Selected model: RandomForestRegressor")
    add_paragraph(doc, "Mean Absolute Error (MAE): 10.60")
    add_paragraph(doc, "Root Mean Squared Error (RMSE): 13.67")
    add_paragraph(doc, "R-squared (R²): 0.893")
    add_paragraph(doc, "Baseline RMSE: 35.58")
    add_paragraph(doc, "The dataset-derived congestion thresholds used after prediction are:")
    add_paragraph(doc, "Low congestion: predicted traffic volume less than or equal to 56.23")
    add_paragraph(doc, "Medium congestion: predicted traffic volume greater than 56.23 and less than or equal to 98.32")
    add_paragraph(doc, "High congestion: predicted traffic volume above 98.32")
    add_table(
        doc,
        ["Model", "MAE", "RMSE", "R-squared"],
        [
            ["LinearRegression (baseline)", f"{metadata.get('baseline_mae', 0):.2f}", f"{metadata.get('baseline_rmse', 0):.2f}", f"{metadata.get('baseline_r2', 0):.3f}"],
            ["RandomForestRegressor", f"{metadata.get('mae', 0):.2f}", f"{metadata.get('rmse', 0):.2f}", f"{metadata.get('r2', 0):.3f}"],
        ],
        [2.5, 1.0, 1.0, 1.1],
    )
    add_paragraph(doc, "Table 3: Regression performance comparison.")
    add_table(
        doc,
        ["Band", "Condition"],
        [
            ["Low", f"Predicted traffic volume <= {congestion_thresholds.get('low_max', 0):.2f}"],
            ["Medium", f"{congestion_thresholds.get('low_max', 0):.2f} < predicted traffic volume <= {congestion_thresholds.get('medium_max', 0):.2f}"],
            ["High", f"Predicted traffic volume > {congestion_thresholds.get('medium_max', 0):.2f}"],
        ],
        [1.3, 4.3],
    )
    add_paragraph(doc, "Table 4: Congestion thresholds derived from predicted traffic volume.")
    add_paragraph(
        doc,
        "From the user-facing perspective, the application translates these regression outputs into a clean prediction panel. The screen shows the predicted traffic volume, the threshold boundaries, the derived congestion level, and explanatory statements that help a commuter understand why a case is classified as risky or relatively safe.",
    )
    add_figure(
        doc,
        prediction_screenshot,
        "Figure 7: Prediction output view showing the regression result and derived congestion band.",
        width_inches=5.9,
    )
    add_paragraph(
        doc,
        "Figure 7 is important from an evaluation perspective because it shows how a continuous regression output is converted into an interpretable decision-support message. The screen presents the predicted traffic volume together with the derived congestion band and explanatory cues, thereby illustrating the practical value of the post-prediction classification strategy adopted in this study. In the current implementation, the frontend can also fall back to a built-in demonstration mode when live services are unavailable, which improves reliability during presentation and testing.",
    )
    add_paragraph(
        doc,
        "The what-if simulation workflow is strengthened by a comparison state that preserves the previous prediction and places it beside the current one. This makes the frontend useful for analytical experimentation because the effect of changing time, weather, or location can be seen immediately without forcing the user to remember earlier results mentally.",
    )
    add_figure(
        doc,
        comparison_screenshot,
        "Figure 8: Scenario comparison view showing what-if simulation results.",
        width_inches=5.9,
    )
    add_paragraph(
        doc,
        "Figure 8 demonstrates the analytical role of the what-if simulation component. By displaying two scenarios side by side, the interface supports comparative reasoning about how changes in explanatory variables alter predicted traffic conditions, which is consistent with the project's decision-support objective and strengthens the usefulness of the system for exploratory transport analysis.",
    )
    add_paragraph(
        doc,
        "Beyond the model error metrics, the broader analytical summary of the dataset also supports the plausibility of the fitted model. The synthetic records are distributed across a wide set of traffic contexts, and the class breakdown implied by the original congestion labels is close to balanced. This matters because it reduces the risk that the regression system is merely overfitting one narrow congestion regime. It also means that the threshold-based mapping from traffic volume to Low, Medium, and High can be interpreted as a reasonably broad summary of the modeled traffic environment rather than a one-sided partition.",
    )
    add_heading(doc, "4.4 Model Interpretation and Analysis of Results", level=2)
    add_paragraph(
        doc,
        "Model interpretation in this study focuses on explaining how the selected Random Forest Regressor reaches useful predictions and how those predictions are translated into decision support outputs. The interpretation layer now includes permutation feature importance, partial dependence plots, LIME local explanation, and SHAP contribution analysis. Together, these methods provide both global and local perspectives on model behavior.",
    )
    add_paragraph(
        doc,
        "Feature importance provides a global ranking of which variables matter most to predictive performance. In the current model, the strongest factors are hour, location, and is_weekend, which suggests that temporal rhythm and place-specific context dominate the model's traffic volume estimates. Partial dependence plots are used to examine the average marginal effect of a selected feature while holding the other features in their observed distribution. This is helpful for identifying whether the model responds smoothly or nonlinearly to variables such as hour or day_of_week.",
    )
    add_paragraph(
        doc,
        "The permutation feature importance profile is especially informative because it is model-agnostic and measures how prediction quality changes when a feature is randomly disrupted. In this project, the very large importance assigned to hour confirms that traffic intensity in the synthetic Lokoja data is highly time-dependent. Location is the next major signal, which aligns with the dataset's spatial structure and with the observation that some zones accumulate far more High-congestion cases than others. Weekend status and day of week also contribute meaningfully, indicating that the model is not using time-of-day alone but is learning a broader weekly traffic rhythm.",
    )
    add_paragraph(
        doc,
        "It is also useful to interpret the lower-ranked variables carefully. Features such as near_commercial_hub, road_type, vehicle_mix, and road_condition appear with much smaller permutation scores, while a few values are slightly negative. In model-interpretation terms, a near-zero or slightly negative permutation score does not automatically mean that the feature is useless in all circumstances; rather, it suggests that within the current fitted model and synthetic data generation process, the feature contributes little additional predictive signal beyond what stronger features already explain. This is an important distinction in an academic report because it avoids overstating weak variables as irrelevant when they may still matter under a richer real-world dataset.",
    )
    if feature_importance:
        ranked = ", ".join(item["feature"] for item in feature_importance[:5])
        add_paragraph(doc, f"The top ranked features from the current permutation importance analysis are {ranked}.")
    if pdp_summary:
        add_paragraph(doc, "The current partial dependence analysis indicates the following:")
        for item in pdp_summary:
            add_paragraph(doc, item)
    add_paragraph(
        doc,
        "The partial dependence plots deepen this interpretation by showing the average directional effect of specific predictors on traffic-volume output. For hour, the plot helps reveal how predicted traffic changes as the day moves from low-activity overnight periods into active commuting and market periods. For day_of_week, the plot provides evidence about how traffic volume shifts across the weekly cycle. Because random forests can model nonlinear interactions, partial dependence is valuable here: it makes the model less of a black box by showing whether the fitted response behaves in a plausible transport-oriented pattern rather than in a purely arbitrary way.",
    )
    add_paragraph(
        doc,
        "LIME is used as a local explanation technique for one prediction instance. It approximates the model locally with an interpretable surrogate and shows which input values push the predicted traffic volume upward or downward for that specific case. SHAP is also used to quantify additive feature contributions. Unlike a simple ranking, SHAP helps show the magnitude of each feature's contribution and supports a more principled explanation of why the model output changes across samples.",
    )
    add_paragraph(
        doc,
        "LIME and SHAP serve complementary roles in the interpretation workflow. LIME is useful when the analyst wants to explain one prediction to a human decision-maker in practical terms. For example, it can show that a particular combination of hour, location, and weekday status pushes a single forecast upward. SHAP, on the other hand, is stronger for consistent additive attribution across many observations because it expresses each feature's contribution in relation to a baseline expectation. In this project, SHAP is especially valuable because it supports a bridge between technical model behavior and the narrative explanations shown to end users.",
    )
    if lime_summary:
        add_paragraph(doc, "For the current sample explanation, LIME identified these notable local contributions:")
        for item in lime_summary[:4]:
            add_paragraph(doc, item)
    if shap_summary:
        add_paragraph(doc, "The current SHAP summary also reinforces the global interpretation pattern, with the highest mean absolute contributions coming from:")
        for item in shap_summary[:4]:
            add_paragraph(doc, item)
    add_paragraph(
        doc,
        "The SHAP summary is broadly consistent with the permutation ranking: hour remains the most influential feature, followed by location and weekend-related timing variables. This cross-method consistency is analytically important because it suggests that the interpretation findings are not artifacts of only one explanation technique. When multiple interpretation methods point to the same dominant variables, the report can discuss those variables with greater confidence, while still acknowledging that the dataset is synthetic and that the conclusions are therefore provisional.",
    )
    add_paragraph(
        doc,
        "Another important layer of interpretation in this project is the post-prediction transformation from traffic volume to congestion class. This step is not merely a cosmetic relabeling. It is the decision-support bridge that converts a continuous regression output into a form that commuters and non-technical stakeholders can understand quickly. The thresholds 56.23 and 98.32 partition the predicted values into low, medium, and high traffic states. In academic terms, this creates a two-stage reasoning chain: first the model estimates a quantitative transport intensity, and then the system maps that estimate into a qualitative risk band. This architecture is stronger than directly predicting labels because it preserves quantitative information for analysis while still supporting simple user communication.",
    )
    add_paragraph(
        doc,
        "The frontend analytics section complements these technical interpretation methods by presenting a more digestible visual summary of model behavior. In practical use, this helps bridge advanced interpretation outputs such as SHAP and permutation importance with the simpler charts and scorecards that a student, supervisor, or non-technical stakeholder can understand quickly during system demonstration.",
    )
    add_figure(
        doc,
        analytics_screenshot,
        "Figure 9: Analytics section of the frontend showing model insight visualization.",
        width_inches=5.9,
    )
    add_paragraph(
        doc,
        "Figure 9 shows that model interpretation has been exposed at the application level rather than left only in offline development notebooks. This is academically relevant because it demonstrates that feature influence and traffic-pattern summaries are not merely technical diagnostics for the developer, but part of the explainability layer presented to end users and project evaluators.",
    )
    add_paragraph(
        doc,
        "From a discussion standpoint, the interpretation results support a coherent story about the synthetic Lokoja traffic environment. Time-of-day appears to be the main organizing signal, specific zones carry different congestion burdens, and weekend or weekday context modifies expected traffic behavior. The model therefore seems to capture an intelligible structure rather than random noise. Nonetheless, the appropriate academic caution remains that these insights describe the behavior of the fitted system on a synthetic dataset, not verified ground-truth traffic operations in Lokoja. The interpretability layer strengthens trust in the prototype, but it does not remove the need for future field data collection and validation.",
    )
    add_paragraph(
        doc,
        "The Random Forest Regressor substantially outperformed the baseline Linear Regression model, indicating that nonlinear relationships exist among the traffic features. The strong R-squared score suggests that the selected feature set captures much of the variation in traffic volume. However, because the dataset is synthetic, these interpretation findings should be presented as internally consistent indicators within the simulated data environment rather than final evidence about actual Lokoja traffic dynamics.",
    )
    if fi_plot and fi_plot.exists():
        add_figure(doc, fi_plot, "Figure 2: Permutation feature importance for the selected regression model.")
    if pdp_plot and pdp_plot.exists():
        add_figure(doc, pdp_plot, "Figure 3: Partial dependence plots showing average marginal feature effects.")
    if lime_plot and lime_plot.exists():
        add_figure(doc, lime_plot, "Figure 4: LIME local explanation for a sample regression prediction.")
    if shap_plot and shap_plot.exists():
        add_figure(doc, shap_plot, "Figure 5: SHAP summary chart using mean absolute contribution values.")
    add_heading(doc, "4.4.1 Analytical Interpretation of Dataset Patterns", level=2)
    add_paragraph(
        doc,
        f"The dataset-level patterns complement the machine learning interpretation. The synthetic data contains approximately {high_total} High, {medium_total} Medium, and {low_total} Low congestion cases in the legacy class field, which indicates a near-balanced simulated environment. Such balance is helpful for analysis because it prevents the study from being dominated by only one regime of traffic behavior.",
    )
    if top_hours:
        hour_text = ", ".join(str(item.get("hour")) for item in top_hours)
        add_paragraph(
            doc,
            f"The hours with the strongest High-congestion counts are {hour_text}. This pattern supports the conclusion that the synthetic Lokoja traffic environment is strongly time-sensitive, with late afternoon and evening pressure appearing especially important. The fact that one morning hour also enters the top group suggests the presence of a commuter rush pattern rather than a purely single-peak day.",
        )
    if top_locations:
        loc_text = ", ".join(item.get("location", "").replace("_", " ") for item in top_locations)
        add_paragraph(
            doc,
            f"At the spatial level, the most congestion-prone zones in terms of High-congestion counts are {loc_text}. This reinforces the importance of location in the trained model and suggests that the synthetic generator embedded meaningful zone-to-zone contrast rather than treating all areas of Lokoja uniformly.",
        )
    add_heading(doc, "4.4.2 System Verification and Integration Testing", level=2)
    add_paragraph(
        doc,
        "The project was also evaluated from a software-engineering perspective, not only from a machine-learning perspective. The backend was tested to ensure that request validation, ML-service communication, and JSON response handling operate correctly. An end-to-end smoke test was performed by starting the Python ML service and Spring Boot backend together, then sending a real prediction request through the backend route. The successful response confirmed that the frontend-facing backend contract, ML inference, explanation generation, and threshold mapping all work together coherently.",
    )
    add_table(
        doc,
        ["Test Area", "Verification Activity", "Outcome"],
        [
            ["Model training", "Compared Linear Regression and Random Forest Regressor on the same split.", "Random forest selected"],
            ["ML API health", "Checked /health and /insights behavior after training.", "Passed"],
            ["Prediction service", "Submitted sample prediction payload to the Python service.", "Passed"],
            ["Backend tests", "Executed Spring Boot test suite with mvn test.", "Passed"],
            ["End-to-end integration", "Sent POST /api/predict through Spring Boot to the Python ML service.", "Passed"],
            ["Response mapping", "Validated backend JSON mapping for predicted volume, level, thresholds, and explanations.", "Passed after DTO/client fix"],
        ],
        [1.4, 3.8, 1.3],
    )
    add_paragraph(doc, "Table 5: Integration and validation test summary.")
    add_heading(doc, "4.5 Discussion", level=2)
    add_paragraph(
        doc,
        "The present results support the feasibility of a localized traffic decision support system for Lokoja. By predicting traffic volume directly and classifying it afterward into congestion bands, the system preserves a more defensible machine learning formulation while still offering user-friendly output. The added interpretation layer strengthens the system because it does not stop at producing a number; it also shows what factors appear to drive the prediction and how the predicted value falls into an understandable congestion range. At the same time, the synthetic dataset means the current discussion must remain careful: the system is academically useful as a prototype and methodological demonstration, but future deployment claims should depend on training and validating the model with real traffic observations from Lokoja.",
    )

    page_break(doc)

    add_heading(doc, "CHAPTER FIVE: SUMMARY, CONCLUSION, AND RECOMMENDATIONS")
    add_heading(doc, "5.1 Summary", level=2)
    add_paragraph(
        doc,
        "This study is developing a modular traffic congestion prediction and decision support system for Lokoja. The current implementation already establishes the machine learning service, dataset-aligned input handling, regression-based traffic volume prediction, congestion-band interpretation logic, and an initial model interpretation layer based on feature importance and explanatory rules.",
    )
    add_heading(doc, "5.2 Conclusion", level=2)
    add_paragraph(
        doc,
        "The current phase of the work shows that machine learning can provide useful transport insight for Lokoja when historical and contextual features are properly organized. The regression formulation recommended by the project supervisor strengthens the methodological consistency of the study by making the model predict a measurable quantity before interpreting it into categories. The inclusion of model interpretation also improves the academic strength of the project by making the model's behavior more explainable. Nevertheless, because the present dataset is synthetic, the strongest conclusion that can be drawn at this stage is that the system architecture and learning approach are promising and technically coherent, not that they have been fully validated for live deployment.",
    )
    add_heading(doc, "5.3 Recommendations", level=2)
    add_paragraph(
        doc,
        "It is recommended that future project stages complete the Spring Boot integration, build the React dashboard, include visual analytics such as traffic trend charts, and conduct practical user evaluation. Most importantly, the synthetic dataset should be replaced or supplemented with real local traffic observations from Lokoja so that both predictive performance and interpretation claims can be validated under real conditions.",
    )
    add_heading(doc, "5.4 Contributions to Knowledge", level=2)
    add_paragraph(
        doc,
        "The project contributes a localized framework for traffic prediction in Lokoja, a decision-support interpretation layer that transforms numeric regression outputs into usable congestion bands, and a modular architecture that can be extended in future work.",
    )
    add_heading(doc, "5.5 Suggestions for Further Research", level=2)
    add_paragraph(
        doc,
        "Further research may investigate larger real-world datasets, temporal sequence models, geospatial heatmaps, adaptive thresholding, and comparative studies between regression and hybrid prediction approaches for Nigerian urban transport scenarios. It would also be valuable to compare different interpretation methods, such as SHAP-based explanation, partial dependence analysis, and counterfactual simulation, once real field data becomes available.",
    )

    page_break(doc)

    add_heading(doc, "REFERENCES")
    add_paragraph(
        doc,
        "This section is intentionally left as a working placeholder and will be updated with verified academic references used in the literature review and methodology chapters. The final version should include current literature on traffic prediction, intelligent transportation systems, regression modeling, random forest learning, explainable artificial intelligence, and decision support systems.",
    )

    page_break(doc)

    add_heading(doc, "APPENDICES")
    add_heading(doc, "Appendix A: Dataset Profile", level=2)
    add_paragraph(
        doc,
        f"The working dataset contains {dataset_profile.get('row_count', 'N/A')} synthetic records. Categorical values include locations such as {', '.join(categorical_options.get('location', []))}; road types {', '.join(categorical_options.get('road_type', []))}; weather states {', '.join(categorical_options.get('weather', []))}; and vehicle mixes {', '.join(categorical_options.get('vehicle_mix', []))}.",
    )
    add_paragraph(
        doc,
        f"Observed numeric ranges include hour {numeric_ranges.get('hour', {}).get('min', 'N/A')} to {numeric_ranges.get('hour', {}).get('max', 'N/A')}, day_of_week {numeric_ranges.get('day_of_week', {}).get('min', 'N/A')} to {numeric_ranges.get('day_of_week', {}).get('max', 'N/A')}, road_condition {numeric_ranges.get('road_condition', {}).get('min', 'N/A')} to {numeric_ranges.get('road_condition', {}).get('max', 'N/A')}, and traffic_volume {numeric_ranges.get('traffic_volume', {}).get('min', 'N/A')} to {numeric_ranges.get('traffic_volume', {}).get('max', 'N/A')}.",
    )
    add_heading(doc, "Appendix B: Sample Prediction Request and Response", level=2)
    add_paragraph(
        doc,
        'Sample request payload: {"hour": 18, "dayOfWeek": 1, "location": "Lokoja_Central_OldMarket", "weather": "Rain", "roadCondition": 2, "roadType": "Urban", "vehicleMix": "Mixed", "nearCommercialHub": 1}.',
    )
    add_paragraph(
        doc,
        'Sample backend response summary: predictedTrafficVolume = 164.85, congestionLevel = "High", with threshold values low_max = 56.23 and medium_max = 98.32, plus explanation statements and normalized model input.',
    )
    add_heading(doc, "Appendix C: Current Interpretation Artifacts", level=2)
    add_paragraph(
        doc,
        "The current implementation generates interpretation artifacts for permutation feature importance, partial dependence plots, LIME local explanation, and SHAP summary analysis. These figures are embedded in Chapter Four and are also preserved in the project artifacts directory for future report revisions and presentation use.",
    )
    add_heading(doc, "Appendix D: Frontend Verification Screenshots", level=2)
    add_paragraph(
        doc,
        "The frontend screenshots captured during live verification are embedded in Chapter Four and summarize the interface states used for testing and presentation. They include the dashboard overview, the prediction output state, the scenario comparison state, and the analytics section. These images help demonstrate that the project has moved beyond backend-only functionality into a coherent end-to-end application experience.",
    )

    doc.save(OUTPUT_PATH)
    print(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
