import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Send } from "lucide-react";

import { askChat } from "../api/api";

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
      const data = await askChat(currentQuestion, 5);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.answer || "No answer returned.",
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
      <h2>Scientific AI Assistant</h2>

      <div className="chat-box">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role} markdown`}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {msg.text}
            </ReactMarkdown>
          </div>
        ))}

        {loading && (
          <div className="message assistant">Thinking with QMOF RAG...</div>
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
