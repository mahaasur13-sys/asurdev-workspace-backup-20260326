import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Star } from 'lucide-react';

interface Props {
  onSubmit: (agentId: string, rating: number, comment: string) => void;
}

export function FeedbackPanel({ onSubmit }: Props) {
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === 0) return;
    onSubmit('synthesizer', rating, comment);
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 3000);
  };

  return (
    <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
      <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
        {submitted ? <ThumbsUp className="w-4 h-4 text-green-400" /> : <Star className="w-4 h-4 text-yellow-400" />}
        {submitted ? 'Thanks for feedback!' : 'Rate this Analysis'}
      </h3>
      {!submitted ? (
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="flex gap-1">
            {[1,2,3,4,5].map(n => (
              <button key={n} type="button" onClick={() => setRating(n)}
                className={`p-1 ${n <= rating ? 'text-yellow-400' : 'text-slate-600'}`}>
                <Star className="w-5 h-5" fill={n <= rating ? 'currentColor' : 'none'} />
              </button>
            ))}
          </div>
          <textarea
            value={comment}
            onChange={e => setComment(e.target.value)}
            placeholder="Optional comment..."
            className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-sm resize-none"
            rows={2}
          />
          <button type="submit" disabled={rating === 0}
            className="w-full bg-purple-600 hover:bg-purple-500 disabled:bg-slate-700 py-2 rounded-lg text-sm font-medium">
            Submit Feedback
          </button>
        </form>
      ) : (
        <p className="text-green-400 text-sm">Your feedback helps us improve!</p>
      )}
    </div>
  );
}
