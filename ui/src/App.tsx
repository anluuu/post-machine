import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar.tsx";
import PostViewer from "./components/PostViewer.tsx";
import RunLog from "./components/RunLog.tsx";

export type Post = { slug: string; title: string; date: string; size: number };

export type RunState = "idle" | "running" | "done" | "error";

export default function App() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [runState, setRunState] = useState<RunState>("idle");
  const [logLines, setLogLines] = useState<string[]>([]);

  const fetchPosts = () =>
    fetch("/api/posts")
      .then((r) => r.json())
      .then(setPosts)
      .catch(console.error);

  useEffect(() => {
    fetchPosts();
  }, []);

  const handleRun = () => {
    setRunState("running");
    setLogLines([]);

    fetch("/api/run", { method: "POST" }).then((res) => {
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      const pump = (): Promise<void> =>
        reader.read().then(({ done, value }) => {
          if (done) return;
          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop() ?? "";
          for (const part of parts) {
            if (!part.startsWith("data:")) continue;
            try {
              const msg = JSON.parse(part.slice(5).trim());
              if (msg.line) setLogLines((prev) => [...prev, msg.line]);
              if (msg.done) {
                setRunState(msg.code === 0 ? "done" : "error");
                fetchPosts();
                return;
              }
            } catch {
              // ignore malformed chunk
            }
          }
          return pump();
        });

      pump().catch(() => setRunState("error"));
    });
  };

  return (
    <div style={styles.root}>
      <Sidebar
        posts={posts}
        selected={selected}
        onSelect={setSelected}
        runState={runState}
        onRun={handleRun}
      />
      <div style={styles.main}>
        {selected ? (
          <PostViewer slug={selected} />
        ) : (
          <div style={styles.empty}>
            <span style={{ color: "var(--text-dim)" }}>select a post</span>
          </div>
        )}
        {runState !== "idle" && (
          <RunLog lines={logLines} state={runState} onDismiss={() => setRunState("idle")} />
        )}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  root: {
    display: "flex",
    height: "100vh",
    overflow: "hidden",
  },
  main: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    position: "relative",
  },
  empty: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 12,
  },
};
