import { useEffect, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Props = { slug: string };

export default function PostViewer({ slug }: Props) {
  const [content, setContent] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setContent(null);
    fetch(`/api/posts/${slug}`)
      .then((r) => r.json())
      .then((d) => setContent(d.content))
      .catch(console.error);
  }, [slug]);

  const handleCopy = () => {
    if (!content) return;
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  if (!content) {
    return (
      <div style={styles.loading}>
        <span style={{ color: "var(--text-dim)" }}>loading…</span>
      </div>
    );
  }

  return (
    <div style={styles.wrapper}>
      <div style={styles.toolbar}>
        <span style={styles.slug}>{slug}</span>
        <button style={styles.copyBtn} onClick={handleCopy}>
          {copied ? "✓ copied" : "copy"}
        </button>
      </div>
      <div style={styles.content}>
        <Markdown remarkPlugins={[remarkGfm]} components={mdComponents}>
          {content}
        </Markdown>
      </div>
    </div>
  );
}

const mdComponents = {
  h1: ({ children }: { children?: React.ReactNode }) => (
    <h1 style={{ fontSize: 18, fontWeight: 500, color: "var(--text-bright)", marginBottom: 16, lineHeight: 1.4 }}>
      {children}
    </h1>
  ),
  h2: ({ children }: { children?: React.ReactNode }) => (
    <h2 style={{ fontSize: 14, fontWeight: 500, color: "var(--accent)", marginTop: 20, marginBottom: 8 }}>
      {children}
    </h2>
  ),
  p: ({ children }: { children?: React.ReactNode }) => (
    <p style={{ marginBottom: 12, lineHeight: 1.7, color: "var(--text)" }}>{children}</p>
  ),
  ul: ({ children }: { children?: React.ReactNode }) => (
    <ul style={{ paddingLeft: 20, marginBottom: 12, color: "var(--text)" }}>{children}</ul>
  ),
  ol: ({ children }: { children?: React.ReactNode }) => (
    <ol style={{ paddingLeft: 20, marginBottom: 12, color: "var(--text)" }}>{children}</ol>
  ),
  li: ({ children }: { children?: React.ReactNode }) => (
    <li style={{ marginBottom: 4, lineHeight: 1.7 }}>{children}</li>
  ),
  strong: ({ children }: { children?: React.ReactNode }) => (
    <strong style={{ color: "var(--text-bright)", fontWeight: 500 }}>{children}</strong>
  ),
  code: ({ children }: { children?: React.ReactNode }) => (
    <code style={{ background: "var(--bg)", padding: "1px 5px", borderRadius: 3, fontSize: 12, color: "var(--accent)" }}>
      {children}
    </code>
  ),
  hr: () => <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "20px 0" }} />,
};

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
  loading: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 12,
  },
  toolbar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "10px 24px",
    borderBottom: "1px solid var(--border)",
    flexShrink: 0,
  },
  slug: {
    fontSize: 11,
    color: "var(--text-dim)",
    letterSpacing: "0.03em",
  },
  copyBtn: {
    padding: "4px 10px",
    background: "transparent",
    border: "1px solid var(--border-bright)",
    color: "var(--text-dim)",
    borderRadius: 3,
    fontSize: 11,
    transition: "all 0.15s",
  },
  content: {
    flex: 1,
    overflowY: "auto",
    padding: "28px 40px 40px",
    maxWidth: 720,
  },
};
