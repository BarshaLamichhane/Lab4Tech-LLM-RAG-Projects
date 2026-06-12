import type { GroundingSource } from '../types';

export function GroundingPipelineSteps({
  sources,
  grounded,
}: {
  sources: GroundingSource[];
  grounded: boolean;
}) {
  const indexed = sources.some((source) => source.indexed);
  const steps = [
    ['1', 'Upload', sources.length ? `${sources.length} verified material file(s)` : 'Waiting for verified material'],
    ['2', 'Chunk', indexed ? 'Documents split into searchable passages' : 'Runs while building the index'],
    ['3', 'Embed', indexed ? 'Passages converted to HuggingFace embeddings' : 'Runs while building the index'],
    ['4', 'Index', indexed ? 'FAISS index is ready' : 'Choose update or recreate'],
    ['5', 'Retrieve', grounded ? 'Relevant chunks selected from your query' : 'Enabled only for grounded material'],
    ['6', 'Generate', grounded ? 'Mistral uses retrieved context only' : 'Mistral uses the normal generation path'],
  ];
  return <div className="grounding-learning-steps">
    {steps.map(([number, title, detail]) => <div key={number}>
      <span>{number}</span>
      <strong>{title}</strong>
      <small>{detail}</small>
    </div>)}
  </div>;
}
