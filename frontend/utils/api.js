export async function simulateLeak() {
  try {
    const res = await fetch('http://127.0.0.1:8000/simulate');
    return await res.json();
  } catch (err) {
    console.error('Simulation failed:', err);
    return null;
  }
}
