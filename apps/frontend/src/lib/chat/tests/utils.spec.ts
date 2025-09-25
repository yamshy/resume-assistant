import { describe, expect, it } from 'vitest';
import {
  buildAttachmentPayload,
  createId,
  formatFileSize,
  stripMarkdown,
} from '../utils';

describe('createId', () => {
  it('creates unique identifiers with the provided prefix', () => {
    const first = createId('test');
    const second = createId('test');
    expect(first).not.toBe(second);
    expect(first.startsWith('test-')).toBe(true);
  });
});

describe('buildAttachmentPayload', () => {
  it('creates a payload with metadata and data', () => {
    const file = new File(['resume'], 'resume.pdf', { type: 'application/pdf' });
    const payload = buildAttachmentPayload(file, 'ZGF0YQ==');
    expect(payload.id.startsWith('file-')).toBe(true);
    expect(payload.name).toBe('resume.pdf');
    expect(payload.type).toBe('application/pdf');
    expect(payload.data).toBe('ZGF0YQ==');
  });
});

describe('formatFileSize', () => {
  it('handles small and large sizes', () => {
    expect(formatFileSize(512)).toBe('512 B');
    expect(formatFileSize(2048)).toBe('2.0 KB');
    expect(formatFileSize(5_242_880)).toBe('5.0 MB');
    expect(formatFileSize(undefined)).toBe('');
  });
});

describe('stripMarkdown', () => {
  it('removes markdown syntax and preserves text', () => {
    const text = stripMarkdown('**Bold** text with [link](https://example.com) and `code`.');
    expect(text).toBe('Bold text with link and code.');
  });
});
