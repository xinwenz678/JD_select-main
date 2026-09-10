import type { ReactNode } from 'react';

interface StatePanelProps {
  kind: 'loading' | 'error' | 'empty' | 'not-found';
  title: string;
  description: string;
  actions?: ReactNode;
}

export function StatePanel({ kind, title, description, actions }: StatePanelProps) {
  return (
    <section className={`state-panel panel state-${kind}`} aria-busy={kind === 'loading'}>
      <span className={`state-symbol ${kind === 'loading' ? 'spinner' : ''}`} aria-hidden="true">
        {kind === 'error' ? '!' : kind === 'not-found' ? '?' : kind === 'empty' ? '—' : ''}
      </span>
      <div role={kind === 'error' ? 'alert' : 'status'} aria-live={kind === 'error' ? 'assertive' : 'polite'}>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      {actions && <div className="actions">{actions}</div>}
    </section>
  );
}
