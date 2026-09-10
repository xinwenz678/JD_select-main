interface SkillListProps {
  title: string;
  skills: readonly string[];
  tone: 'matched' | 'missing';
  emptyText: string;
}

export function SkillList({ title, skills, tone, emptyText }: SkillListProps) {
  const uniqueSkills = [...new Set(skills)];
  return (
    <section className={`panel skill-panel ${tone}`}>
      <div className="section-heading">
        <h2>{title}</h2><span className="count">{uniqueSkills.length} 项</span>
      </div>
      {uniqueSkills.length > 0 ? (
        <ul className="tags" aria-label={title}>
          {uniqueSkills.map((skill) => <li key={skill}>{skill}</li>)}
        </ul>
      ) : <p className="muted">{emptyText}</p>}
    </section>
  );
}
