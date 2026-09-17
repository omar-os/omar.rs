export function createSwarm(
  count: number,
  width: number,
  random = Math.random,
) {
  const agents = Array.from({ length: count }, (_, i) => ({
    x: 55 + ((i % 9) / 8) * (width - 110),
    y: 65 + Math.floor(i / 9) * 120,
    born: -random() * 3000,
    life: 2200 + random() * 2200,
    phase: random() * Math.PI * 2,
  }));
  const edges = Array.from({ length: count }, (_, i) => ({
    from: i,
    to: (i + 5) % count,
    born: -random() * 1000,
    life: 800 + random() * 1600,
    bend: (random() - 0.5) * 160,
    direction: random() < 0.5 ? -1 : 1,
    speed: 25 + random() * 20,
  }));
  return {
    sample(time: number) {
      const positions = agents.map((agent, i) => {
        if (time >= agent.born + agent.life) {
          agent.born = time + 250 + random() * 700;
          agent.life = 2200 + random() * 2200;
          // Respawn somewhere else, with space around other agent centers.
          for (let attempt = 0; attempt < 20; attempt++) {
            agent.x = 50 + random() * (width - 100);
            agent.y = 50 + random() * 410;
            if (
              agents.every(
                (other, j) =>
                  i === j ||
                  Math.hypot(other.x - agent.x, other.y - agent.y) > 55,
              )
            )
              break;
          }
        }
        const age = time - agent.born;
        const opacity = Math.max(
          0,
          Math.min(1, age / 220, (agent.life - age) / 300),
        );
        return {
          x: agent.x + Math.sin(time / 1400 + agent.phase) * 16,
          y: agent.y + Math.cos(time / 1700 + agent.phase) * 16,
          opacity,
          scale: 0.55 + opacity * 0.45,
        };
      });
      const links = edges.map((edge) => {
        if (
          time >= edge.born + edge.life ||
          positions[edge.from].opacity < 0.1 ||
          positions[edge.to].opacity < 0.1
        ) {
          const candidates: [number, number][] = [];
          positions.forEach((a, i) =>
            positions.forEach((b, j) => {
              if (
                i < j &&
                a.opacity > 0.2 &&
                b.opacity > 0.2 &&
                !edges.some(
                  (other) =>
                    (other.from === i && other.to === j) ||
                    (other.from === j && other.to === i),
                )
              )
                candidates.push([i, j]);
            }),
          );
          const pair = candidates[Math.floor(random() * candidates.length)];
          if (pair) [edge.from, edge.to] = pair;
          edge.born = time;
          edge.life = 800 + random() * 1600;
          edge.bend = (random() - 0.5) * 160;
          edge.direction = random() < 0.5 ? -1 : 1;
        }
        const a = positions[edge.from],
          b = positions[edge.to];
        const age = time - edge.born;
        const fade = Math.max(
          0,
          Math.min(1, age / 200, (edge.life - age) / 200),
        );
        const distance = Math.hypot(b.x - a.x, b.y - a.y) || 1;
        const cx = (a.x + b.x) / 2 - ((b.y - a.y) / distance) * edge.bend;
        const cy = (a.y + b.y) / 2 + ((b.x - a.x) / distance) * edge.bend;
        return {
          from: edge.from,
          to: edge.to,
          path: `M${a.x} ${a.y} Q${cx} ${cy} ${b.x} ${b.y}`,
          opacity: Math.min(a.opacity, b.opacity) * fade * 0.5,
          offset: ((-edge.direction * age) / 1000) * edge.speed,
        };
      });
      return { positions, links };
    },
  };
}
