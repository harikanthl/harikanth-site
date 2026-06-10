const WORDS_PER_MINUTE = 220;

export function readingTime(text: string) {
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  const minutes = Math.max(1, Math.ceil(words / WORDS_PER_MINUTE));
  return { words, minutes, label: `${minutes} min read` };
}
