export const SITE = {
  name: 'Harikanth Lingutla',
  title: 'Harikanth Lingutla — AI/ML Engineer',
  description:
    'I build practical AI systems, GPU projects, and software tools. Writing about PyTorch, CUDA, Triton, and building AI products.',
  url: 'https://harikanth.site',
  email: 'hello@harikanth.site',
  github: 'https://github.com/harikanthl',
  linkedin: 'https://www.linkedin.com/in/mandelbrotset88/',
} as const;

export type SeoProps = {
  title?: string;
  description?: string;
  image?: string;
  type?: 'website' | 'article';
  publishedTime?: string;
  tags?: string[];
};

export function pageTitle(title?: string) {
  return title ? `${title} · ${SITE.name}` : SITE.title;
}

export function canonicalUrl(path: string) {
  return new URL(path, SITE.url).href;
}

export function jsonLdPerson() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Person',
    name: SITE.name,
    url: SITE.url,
    sameAs: [SITE.github, SITE.linkedin],
    jobTitle: 'AI/ML Engineer',
  };
}

export function jsonLdBlogPosting(post: {
  title: string;
  description: string;
  url: string;
  date: Date;
  tags: string[];
  image?: string;
}) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: post.title,
    description: post.description,
    url: post.url,
    datePublished: post.date.toISOString(),
    author: { '@type': 'Person', name: SITE.name, url: SITE.url },
    keywords: post.tags.join(', '),
    ...(post.image ? { image: post.image } : {}),
  };
}

export function jsonLdSoftware(project: {
  title: string;
  description: string;
  url: string;
  tech: string[];
}) {
  return {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: project.title,
    description: project.description,
    url: project.url,
    applicationCategory: 'DeveloperApplication',
    operatingSystem: 'Web',
    programmingLanguage: project.tech,
  };
}
