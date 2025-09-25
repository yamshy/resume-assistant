import { fireEvent, render } from '@testing-library/svelte'
import { tick } from 'svelte'
import MessageInput from '../MessageInput.svelte'
import type { SendMessageOptions } from '../types'

describe('MessageInput', () => {
  it('emits submit events with the current content and resets the form', async () => {
    const submissions: SendMessageOptions[] = []
    const { getByRole } = render(MessageInput, {
      events: {
        submit: (event: CustomEvent<SendMessageOptions>) => {
          submissions.push(event.detail)
        }
      }
    })
    const textarea = getByRole('textbox', { name: /chat input/i }) as HTMLTextAreaElement
    const submitButton = getByRole('button', { name: /send/i })

    await fireEvent.input(textarea, { target: { value: 'Hello resume assistant' } })
    await fireEvent.click(submitButton)
    await tick()

    expect(submissions).toHaveLength(1)
    expect(submissions[0].content).toBe('Hello resume assistant')
    expect(submissions[0].files ?? []).toEqual([])
    expect(textarea).toHaveValue('')
    expect(submitButton).toBeDisabled()
  })

  it('supports attaching files before submitting', async () => {
    const submissions: SendMessageOptions[] = []
    const { getByLabelText, getByRole, queryByText } = render(MessageInput, {
      events: {
        submit: (event: CustomEvent<SendMessageOptions>) => {
          submissions.push(event.detail)
        }
      }
    })

    const fileInput = getByLabelText('Attach files') as HTMLInputElement
    const submitButton = getByRole('button', { name: /send/i })

    const resume = new File(['content'], 'resume.pdf', { type: 'application/pdf' })
    await fireEvent.change(fileInput, { target: { files: [resume] } })

    expect(queryByText('resume.pdf')).toBeInTheDocument()
    expect(submitButton).not.toBeDisabled()

    await fireEvent.click(submitButton)
    await tick()

    expect(submissions).toHaveLength(1)
    expect(submissions[0].files ?? []).toHaveLength(1)
    expect(submissions[0].files?.[0]?.name).toBe('resume.pdf')
    expect(queryByText('resume.pdf')).not.toBeInTheDocument()
  })

  it('can hide the file upload affordance', () => {
    const { queryByText, queryByLabelText } = render(MessageInput, {
      allowFileUpload: false
    })

    expect(queryByText('Attach files')).not.toBeInTheDocument()
    expect(queryByLabelText('Attach files')).not.toBeInTheDocument()
  })
})
