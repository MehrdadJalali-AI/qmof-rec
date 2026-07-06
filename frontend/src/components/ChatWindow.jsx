import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Send, Bot } from "lucide-react";

import { askChat, recommendMaterials } from "../api/api";
import RecommendationArtifact from "./RecommendationArtifact";

// Heuristic: queries that ask for material suggestions also trigger the
// recommendation pipeline, rendering candidate cards inline as an artifact.
const RECOMMENDATION_KEYWORDS = [
  "recommend",
  "suggest",
  "candidate",
  "find materials",
  "find mofs",
  "find a mof",
  "best mof",
  "top mof",
  "which mof",
  "which mofs",
];

function looksLikeRecommendationQuery(text) {
  const lower = text.toLowerCase();
  return RECOMMENDATION_KEYWORDS.some((kw) => lower.includes(kw));
}

export default function ChatWindow() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Ask me about MOFs, QMOF materials, band gaps, gas adsorption, photocatalysis, or material recommendations.",
    },
  ]);
  const [loading, setLoading] = useState(false);

  async function sendMessage() {
    if (!question.trim()) return;

    const currentQuestion = question;
    const wantsRecommendation = looksLikeRecommendationQuery(currentQuestion);

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        text: currentQuestion,
      },
    ]);

    setQuestion("");
    setLoading(true);

    try {
      const chatPromise = askChat(currentQuestion);

      const recommendPromise = wantsRecommendation
        ? recommendMaterials(currentQuestion, 5).catch((err) => {
            console.error("Recommendation failed:", err);
            return null;
          })
        : Promise.resolve(null);

      const [chatData, recommendData] = await Promise.all([
        chatPromise,
        recommendPromise,
      ]);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: chatData.answer || "No answer returned.",
          artifact: recommendData,
          artifactQuery: currentQuestion,
        },
      ]);
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Chat request failed. Please check backend logs.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card">
      <h2>
        <Bot size={20} />
        Scientific AI Assistant
      </h2>

      <div className="chat-box">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {msg.text}
              </ReactMarkdown>
            </div>

            {msg.artifact && (
              <RecommendationArtifact
                data={msg.artifact}
                query={msg.artifactQuery}
              />
            )}
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="markdown">Thinking with QMOF RAG...</div>
          </div>
        )}
      </div>

      <textarea
        className="textarea"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask: Which MOFs are suitable for photocatalysis?"
        onKeyDown={(e) => {
          if (e.key === "Enter" && e.ctrlKey) {
            sendMessage();
          }
        }}
      />

      <button className="primary-btn" onClick={sendMessage}>
        <Send size={16} /> Ask
      </button>
    </section>
  );
}
