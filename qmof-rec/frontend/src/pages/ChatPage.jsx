import ChatWindow from "../components/ChatWindow";

export default function ChatPage() {
  return (
    <>
      <div className="header">
        <div>
          <div className="page-title">Scientific Chat</div>
          <div className="subtitle">
            Ask research questions over QMOF retrieval context.
          </div>
        </div>
      </div>

      <ChatWindow />
    </>
  );
}
