import type { Post, RunState } from "../App.tsx";

type Props = {
  posts: Post[];
  selected: string | null;
  onSelect: (slug: string) => void;
  runState: RunState;
  onRun: () => void;
};

export default function Sidebar({ posts, selected, onSelect, runState, onRun }: Props) {
  const running = runState === "running";

  return (
    <aside style={styles.sidebar}>
      <div style={styles.header}>
        <span style={styles.logo}>posts</span>
        <span style={styles.count}>{posts.length}</span>
      </div>

      <div style={styles.list}>
        {posts.map((p) => (
          <button
            key={p.slug}
            style={{
              ...styles.item,
              ...(selected === p.slug ? styles.itemSelected : {}),
            }}
            onClick={() => onSelect(p.slug)}
          >
            <span style={styles.date}>{p.date}</span>
            <span style={styles.title}>{p.title}</span>
          </button>
        ))}
      </div>

      <div style={styles.footer}>
        <button
          style={{ ...styles.runBtn, ...(running ? styles.runBtnActive : {}) }}
          onClick={onRun}
          disabled={running}
        >
          {running ? "● running…" : "▶ run agent"}
        </button>
      </div>
    </aside>
  );
}

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    width: "var(--sidebar-w)",
    minWidth: "var(--sidebar-w)",
    background: "var(--bg-panel)",
    borderRight: "1px solid var(--border)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
  header: {
    padding: "16px 16px 12px",
    borderBottom: "1px solid var(--border)",
    display: "flex",
    alignItems: "baseline",
    gap: 8,
  },
  logo: {
    fontSize: 13,
    color: "var(--accent)",
    fontWeight: 500,
    letterSpacing: "0.05em",
  },
  count: {
    fontSize: 11,
    color: "var(--text-dim)",
  },
  list: {
    flex: 1,
    overflowY: "auto",
    padding: "4px 0",
  },
  item: {
    display: "block",
    width: "100%",
    textAlign: "left",
    padding: "8px 16px",
    background: "transparent",
    color: "var(--text)",
    borderRadius: 0,
    transition: "background 0.1s",
    cursor: "pointer",
  },
  itemSelected: {
    background: "var(--bg-selected)",
    color: "var(--text-bright)",
  },
  date: {
    display: "block",
    fontSize: 10,
    color: "var(--text-dim)",
    marginBottom: 2,
  },
  title: {
    display: "block",
    fontSize: 12,
    lineHeight: 1.4,
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  footer: {
    padding: "12px 16px",
    borderTop: "1px solid var(--border)",
  },
  runBtn: {
    width: "100%",
    padding: "8px 12px",
    background: "transparent",
    border: "1px solid var(--accent-dim)",
    color: "var(--accent)",
    borderRadius: 3,
    fontSize: 12,
    letterSpacing: "0.05em",
    transition: "all 0.15s",
  },
  runBtnActive: {
    color: "var(--text-dim)",
    borderColor: "var(--border-bright)",
    cursor: "not-allowed",
  },
};
