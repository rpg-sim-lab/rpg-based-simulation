import React from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';

const SPACES = [
  {
    to: '/wiki/world-knowledge',
    title: 'World Knowledge',
    text: 'The laws of the world, the mechanisms that move it, and who and what lives in it.',
  },
  {
    to: '/wiki/technical',
    title: 'Technical',
    text: 'How the engine works. Coming later.',
  },
  {
    to: '/wiki/control-guide',
    title: 'Control Guide',
    text: 'How to run, watch and replay a simulation. Coming later.',
  },
];

export default function Home() {
  return (
    <Layout title="RPG Simulation Wiki" description="What happens in the simulated world, and why">
      <main style={{padding: '2rem', maxWidth: '900px', margin: '0 auto'}}>
        <h1>RPG Simulation Wiki</h1>
        <p>
          A world that runs by itself: beings with needs, goals and partial knowledge, factions,
          settlements and an economy, all following the same laws. This wiki explains what you are
          seeing while it runs.
        </p>
        {SPACES.map((space) => (
          <section key={space.to} style={{marginTop: '1.5rem'}}>
            <h2><Link to={space.to}>{space.title}</Link></h2>
            <p>{space.text}</p>
          </section>
        ))}
      </main>
    </Layout>
  );
}
