import React, { useState, useMemo } from "react";
import { Flag, Plus, X, ClipboardList, Languages } from "lucide-react";

const FONTS = `
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
`;

const INK = "#1C2321";
const PAPER = "#EDEEE7";
const RULE = "#B8BBAE";
const TEAL = "#2F5D62";
const SLATE = "#44506B";
const AMBER = "#A85A1E";

const VISIT_THRESHOLD = 10;
const WISH_THRESHOLD = 2;

const STRINGS = {
  zh: {
    title: "升級路由檢核",
    subtitle: "結構性缺口偵測 — 僅供複核參考",
    intakeTitle: "案件基本資料",
    intakeSub: "輸入既有紀錄中已存在的數值，不需新增判斷。",
    days: "通報後天數",
    visits: "累計訪視 / 聯繫次數",
    wishes: "兒童表意想被安置次數",
    judicial: "司法保護安置門檻",
    judicialOpts: { unclear: "尚未確認", no: "未達成", yes: "已達成" },
    refused: "兒童曾拒絕特定安置型態（如大型機構）",
    actorsTitle: "涉案人員類型",
    add: "新增",
    actorPlaceholder: "例：母親的性交易對象",
    covered: "已列入現行評估",
    submit: "產生升級路由紀錄",
    ledgerTitle: "升級路由紀錄",
    ledgerSub: "依左側資料比對規則，逐筆列出結構性缺口與應複核對象。",
    beforeSubmit: "尚未產生紀錄。填妥左側資料後按「產生升級路由紀錄」。",
    noFindings: "依現有輸入，未偵測到結構性缺口。這不代表個案已妥善處理，僅代表本工具設定的規則未被觸發。",
    targetLabel: "應複核對象：",
    footer: "本工具僅偵測結構性缺口與升級路由對象，不判斷是否安置、事件是否成立，或任何個案的最終處置。所有輸出均須由具權責之人員複核；規則觸發不等於結論成立，未觸發也不等於個案無虞。",
  },
  en: {
    title: "Escalation Routing Check",
    subtitle: "Structural gap detection — for review reference only",
    intakeTitle: "Case intake data",
    intakeSub: "Enter values already present in existing records — no new judgment needed.",
    days: "Days since report",
    visits: "Total visits / contacts logged",
    wishes: "Times child expressed wish to be placed",
    judicial: "Judicial protective threshold",
    judicialOpts: { unclear: "Unconfirmed", no: "Not met", yes: "Met" },
    refused: "Child has refused a specific placement type (e.g. large institution)",
    actorsTitle: "Actor types involved",
    add: "Add",
    actorPlaceholder: "e.g. mother's trafficking associate",
    covered: "Covered by current assessment",
    submit: "Generate escalation record",
    ledgerTitle: "Escalation routing record",
    ledgerSub: "Rules are checked against the intake data; each match is listed as a structural gap with its review target.",
    beforeSubmit: "No record generated yet. Fill in the intake form, then press \u201cGenerate escalation record.\u201d",
    noFindings: "No structural gap detected from current inputs. This does not mean the case is handled well — only that none of this tool's rules were triggered.",
    targetLabel: "Review target:",
    footer: "This tool only detects structural gaps and escalation targets. It does not determine whether placement is warranted, whether an incident occurred, or any case's final disposition. All output requires review by an accountable person; a triggered rule is not a conclusion, and no trigger does not mean the case is fine.",
  },
};

function evaluateRaw(state) {
  const findings = [];

  state.actors.forEach((a) => {
    if (a.label.trim() && !a.covered) {
      findings.push({ type: "R1", label: a.label, color: AMBER });
    }
  });

  if (state.visitCount >= VISIT_THRESHOLD && state.wishCount >= WISH_THRESHOLD) {
    findings.push({ type: "R2", visitCount: state.visitCount, wishCount: state.wishCount, color: AMBER });
  }

  if (state.wishCount >= 1 && state.refusedInstitutional) {
    findings.push({ type: "R3", color: AMBER });
  }

  if (state.judicialThreshold === "unclear") {
    findings.push({ type: "R4", color: AMBER });
  }

  return findings;
}

function renderFinding(f, lang) {
  const t =
    lang === "zh"
      ? {
          R1: {
            code: "R1 · SCOPE_DESIGN_GAP",
            description: `涉案人員類型「${f.label}」未被現行風險評估類別涵蓋`,
            target: "風險評估類別 / 政策制定者（督導或政策層）",
            rationale: "這是分類規則本身的涵蓋範圍缺口，不是個別社工的判斷失誤。",
          },
          R2: {
            code: "R2 · ACCUMULATION_NOT_ESCALATED",
            description: `累計 ${f.visitCount} 次訪視、${f.wishCount} 次兒童表意想被安置，未查見對應之升級複核紀錄`,
            target: "督導 / 單位主管",
            rationale: "重複性求助累積已超過單次評估的合理範圍，結構上應觸發強制複核，而非逐次獨立判斷。",
          },
          R3: {
            code: "R3 · PREFERENCE_DIMENSION_COLLAPSE",
            description: "兒童曾表達想被安置，同時曾拒絕特定安置型態（如大型機構）——這是兩個不同維度的偏好",
            target: "個案會議（應評估多元安置選項）",
            rationale: "拒絕特定型態不等於拒絕安置本身，何者優先是價值判斷，本工具不代為認定。",
          },
          R4: {
            code: "R4 · AUTHORITY_THRESHOLD_UNDEFINED",
            description: "司法保護安置門檻是否已達成，尚未確認",
            target: "法律顧問 / 主管機關法制單位",
            rationale: "門檻認定屬法律判斷，非結構性工具可代為認定。",
          },
        }
      : {
          R1: {
            code: "R1 · SCOPE_DESIGN_GAP",
            description: `Actor type "${f.label}" is not covered by the current risk-assessment categories`,
            target: "Risk-assessment schema owner / policy layer (supervisor or above)",
            rationale: "This is a gap in the classification schema itself, not an individual social worker's misjudgment.",
          },
          R2: {
            code: "R2 · ACCUMULATION_NOT_ESCALATED",
            description: `${f.visitCount} logged visits and ${f.wishCount} expressed wishes to be placed, with no corresponding escalation review found`,
            target: "Supervisor / unit lead",
            rationale: "Repeated signals have exceeded the reasonable scope of a single-instance evaluation; structurally this should trigger mandatory review, not repeated independent assessment.",
          },
          R3: {
            code: "R3 · PREFERENCE_DIMENSION_COLLAPSE",
            description: "Child expressed wanting to be placed while also refusing a specific placement type (e.g. a large institution) — these are two different preference dimensions",
            target: "Case conference (should evaluate alternative placement options)",
            rationale: "Refusing a specific type is not the same as refusing placement itself; which one takes priority is a value judgment this tool does not make.",
          },
          R4: {
            code: "R4 · AUTHORITY_THRESHOLD_UNDEFINED",
            description: "Whether the judicial protective-placement threshold has been met is unconfirmed",
            target: "Legal counsel / regulatory legal affairs unit",
            rationale: "Threshold determination is a legal judgment, not something a structural tool can establish.",
          },
        };
  return { ...t[f.type], color: f.color };
}

export default function EscalationRoutingTool() {
  const [lang, setLang] = useState("zh");
  const s = STRINGS[lang];

  const [days, setDays] = useState("");
  const [visitCount, setVisitCount] = useState("");
  const [wishCount, setWishCount] = useState("");
  const [refusedInstitutional, setRefusedInstitutional] = useState(false);
  const [judicialThreshold, setJudicialThreshold] = useState("unclear");
  const [actors, setActors] = useState([{ label: "", covered: true }]);
  const [submitted, setSubmitted] = useState(false);

  const findings = useMemo(
    () =>
      evaluateRaw({
        visitCount: Number(visitCount) || 0,
        wishCount: Number(wishCount) || 0,
        refusedInstitutional,
        judicialThreshold,
        actors,
      }).map((f) => renderFinding(f, lang)),
    [visitCount, wishCount, refusedInstitutional, judicialThreshold, actors, lang]
  );

  const updateActor = (i, field, value) => {
    const next = actors.slice();
    next[i] = { ...next[i], [field]: value };
    setActors(next);
  };

  const addActor = () => setActors([...actors, { label: "", covered: true }]);
  const removeActor = (i) => setActors(actors.filter((_, idx) => idx !== i));

  return (
    <div style={{ background: PAPER, color: INK, minHeight: "100vh", fontFamily: "'IBM Plex Sans', sans-serif" }}>
      <style>{FONTS}</style>

      <header style={{ borderBottom: `2px solid ${INK}` }} className="px-6 md:px-10 py-5 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 style={{ fontFamily: "'Source Serif 4', serif" }} className="text-2xl md:text-3xl font-semibold tracking-tight">
            {s.title}
          </h1>
          <span style={{ color: SLATE }} className="text-sm">{s.subtitle}</span>
        </div>
        <button
          onClick={() => setLang(lang === "zh" ? "en" : "zh")}
          className="flex items-center gap-1.5 text-sm px-3 py-1.5"
          style={{ border: `1px solid ${INK}`, color: INK }}
        >
          <Languages size={14} />
          {lang === "zh" ? "English" : "中文"}
        </button>
      </header>

      <main className="grid md:grid-cols-2 gap-0" style={{ minHeight: "calc(100vh - 84px)" }}>
        {/* Intake column */}
        <section className="p-6 md:p-10 space-y-8" style={{ borderRight: `2px solid ${RULE}` }}>
          <div>
            <h2 style={{ fontFamily: "'Source Serif 4', serif" }} className="text-lg font-semibold mb-1">
              {s.intakeTitle}
            </h2>
            <p style={{ color: SLATE }} className="text-sm">{s.intakeSub}</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field label={s.days}>
              <input type="number" min="0" value={days} onChange={(e) => setDays(e.target.value)} style={inputStyle} />
            </Field>
            <Field label={s.visits}>
              <input type="number" min="0" value={visitCount} onChange={(e) => setVisitCount(e.target.value)} style={inputStyle} />
            </Field>
            <Field label={s.wishes}>
              <input type="number" min="0" value={wishCount} onChange={(e) => setWishCount(e.target.value)} style={inputStyle} />
            </Field>
            <Field label={s.judicial}>
              <select value={judicialThreshold} onChange={(e) => setJudicialThreshold(e.target.value)} style={inputStyle}>
                <option value="unclear">{s.judicialOpts.unclear}</option>
                <option value="no">{s.judicialOpts.no}</option>
                <option value="yes">{s.judicialOpts.yes}</option>
              </select>
            </Field>
          </div>

          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={refusedInstitutional} onChange={(e) => setRefusedInstitutional(e.target.checked)} />
            {s.refused}
          </label>

          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 style={{ fontFamily: "'Source Serif 4', serif" }} className="font-semibold">{s.actorsTitle}</h3>
              <button onClick={addActor} className="flex items-center gap-1 text-sm" style={{ color: TEAL }}>
                <Plus size={14} /> {s.add}
              </button>
            </div>
            <div className="space-y-2">
              {actors.map((a, i) => (
                <div key={i} className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder={s.actorPlaceholder}
                    value={a.label}
                    onChange={(e) => updateActor(i, "label", e.target.value)}
                    style={{ ...inputStyle, flex: 1 }}
                  />
                  <label className="flex items-center gap-1 text-xs whitespace-nowrap" style={{ color: SLATE }}>
                    <input type="checkbox" checked={a.covered} onChange={(e) => updateActor(i, "covered", e.target.checked)} />
                    {s.covered}
                  </label>
                  {actors.length > 1 && (
                    <button onClick={() => removeActor(i)} style={{ color: SLATE }}>
                      <X size={14} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={() => setSubmitted(true)}
            style={{ background: INK, color: PAPER }}
            className="px-5 py-2.5 text-sm font-medium"
          >
            {s.submit}
          </button>
        </section>

        {/* Ledger column */}
        <section className="p-6 md:p-10 flex flex-col">
          <h2 style={{ fontFamily: "'Source Serif 4', serif" }} className="text-lg font-semibold mb-1">
            {s.ledgerTitle}
          </h2>
          <p style={{ color: SLATE }} className="text-sm mb-6">{s.ledgerSub}</p>

          <div className="flex-1 space-y-4">
            {!submitted ? (
              <div className="text-sm" style={{ color: SLATE }}>{s.beforeSubmit}</div>
            ) : findings.length === 0 ? (
              <div className="text-sm" style={{ color: SLATE }}>{s.noFindings}</div>
            ) : (
              findings.map((f, i) => (
                <div key={i} style={{ borderLeft: `3px solid ${f.color}` }} className="pl-4 py-1">
                  <div className="flex items-center gap-2 text-xs font-medium" style={{ color: f.color }}>
                    <Flag size={12} />
                    {f.code}
                  </div>
                  <p className="text-sm mt-1">{f.description}</p>
                  <p className="text-sm mt-1" style={{ color: SLATE }}>
                    <span style={{ color: TEAL, fontWeight: 600 }}>{s.targetLabel}</span>
                    {f.target}
                  </p>
                  <p className="text-xs mt-1" style={{ color: SLATE }}>{f.rationale}</p>
                </div>
              ))
            )}
          </div>
        </section>
      </main>

      <footer style={{ borderTop: `2px solid ${INK}`, background: INK, color: PAPER }} className="px-6 md:px-10 py-4 text-xs flex items-start gap-2">
        <ClipboardList size={14} className="mt-0.5 shrink-0" />
        <span>{s.footer}</span>
      </footer>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="block text-sm">
      <span style={{ color: SLATE }} className="block mb-1">{label}</span>
      {children}
    </label>
  );
}

const inputStyle = {
  width: "100%",
  padding: "0.5rem 0.65rem",
  border: `1px solid ${RULE}`,
  background: "#fff",
  fontSize: "0.9rem",
  color: INK,
};
