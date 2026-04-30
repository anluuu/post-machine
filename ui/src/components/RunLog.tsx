import { useEffect, useRef } from "react";
import type { RunState } from "../App.tsx";

type Props = {
  lines: string[];
  state: RunState;
  onDismiss: () => void;
};

export default function RunLog({ lines, state, onDismiss }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  const stateColor =
    state === "running" ? "var(--text-dim)" :
    state === "done"    ? "var(--accent)" :
                          "var(--danger)";

  const stateLabel =
    state === "running" ? "● running" :
    state === "done"    ? "✓ done" :
                          "✗ error";

  return (
    <div style={styles.panel}>
      <div style={styles.header}>
        <span style={{ ...styles.status, color: stateColor }}>{stateLabel}</span>
        <button style={styles.dismiss} onClick={onDismiss}>
          ✕
        </button>
      </div>
      <div style={styles.log}>
        {lines.map((line, i) => (
          <div key={i} style={styles.line}>
            {line}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  panel: {
    borderTop: "1px solid var(--border)",
    background: "var(--bg-panel)",
    display: "flex",
    flexDirection: "column",
    height: 200,
    flexShrink: 0,
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "6px 16px",
    borderBottom: "1px solid var(--border)",
    flexShrink: 0,
  },
  status: {
    fontSize: 11,
    letterSpacing: "0.05em",
  },
  dismiss: {
    background: "transparent",
    color: "var(--text-dim)",
    fontSize: 11,
    padding: "2px 4px",
    borderRadius: 2,
  },
  log: {
    flex: 1,
    overflowY: "auto",
    padding: "8px 16px",
    fontFamily: "var(--font)",
    fontSize: 11,
    lineHeight: 1.7,
  },
  line: {
    color: "var(--text)",
    whiteSpace: "pre-wrap",
    wordBreak: "break-all",
  },
};
