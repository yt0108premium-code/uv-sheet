import { CheckCircle2, XCircle } from 'lucide-react';

export default function Toast({ message, error, action }: { message: string; error?: boolean; action?: () => void }) {
  return <div className={`toast ${error ? 'error' : ''}`}>{error ? <XCircle size={19} /> : <CheckCircle2 size={19} />}<span>{message}</span>{action && <button onClick={action}>Show file</button>}</div>;
}
