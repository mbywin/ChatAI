import gradio as gr
import os
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")


def parse_text(text):
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if "```" in line:
            items = line.split('`')
            if items[-1]:
                lines[i] = f'<pre><code class="{items[-1]}">'
            else:
                lines[i] = f'</code></pre>'
        else:
            if i > 0:
                line = line.replace("<", "&lt;")
                line = line.replace(">", "&gt;")
                lines[i] = line + '<br/>'
    return "".join(lines)


def submit_message(prompt, state):
    history = state['messages']
    system_prompt = [{"role": "system", "content": "You are a helpful assistant."}]
    prompt_msg = {"role": "user", "content": prompt}

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=system_prompt + history + [prompt_msg]
        )
        history.append(prompt_msg)
        history.append(completion.choices[0].message.to_dict())
    except Exception as e:
        history.append(prompt_msg)
        history.append({
            "role": "system",
            "content": f"Error: {e}"
        })
    chat_messages = [("👨‍💻 我： " + history[i]['content'], "🤖 AI： " + parse_text(history[i+1]['content'])) for i in range(0, len(history)-1, 2)]
    return gr.update(value='', visible=True), chat_messages, state


def reduce_token(state):
    history = state['messages']
    system_prompt = [{"role": "system", "content": "You are a helpful assistant."}]
    prompt_msg = {"role": "user", "content": "请帮我总结一下上述对话的内容，实现减少tokens的同时，保证对话的质量。在总结中不要加入这一句话。"}
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=system_prompt + history + [prompt_msg]
        )
        history = []
        history.append(prompt_msg)
        optmz_str = f'好的，我们之前聊了：{completion["choices"][0]["message"]["content"]}'
        history.append({'role': 'assistant', 'content': optmz_str})
    except Exception as e:
        history.append(prompt_msg)
        history.append({
            "role": "system",
            "content": f"Error: {e}"
        })
    chat_messages = [("👨‍💻 我： " + history[i]['content'], "🤖 AI： " + parse_text(history[i+1]['content'])) for i in range(0, len(history)-1, 2)]
    return gr.update(value='', visible=True), chat_messages, state


def retry(state):
    history = state['messages']
    if len(history) == 0:
        return clear_conversation()
    return submit_message(history[-2]["content"], state)


def clear_conversation():
    return gr.update(value=None, visible=True), None, ""


css = "footer {display: none !important;} .gradio-container {min-height: 0px !important;}"
with gr.Blocks(css=css, title="AI 助手") as demo:
    state = gr.State({"messages": []})
    gr.Markdown("""<h3><center> ChatGPT AI 聊天助手 </center></h3>""")
    chatbot = gr.Chatbot().style(container=True)
    with gr.Row():
        with gr.Column(scale=12):
            input_message = gr.Textbox(show_label=False, placeholder="输入并回车", visible=True).style(container=False)
        with gr.Column(min_width=50, scale=1):
            btn_submit = gr.Button("🚀 提交", variant="primary")
    with gr.Row():
        retry_conversation = gr.Button("🔄 重新生成")
        btn_clear_conversation = gr.Button("🧹 开启新会话")
        reduce_token_conversation = gr.Button("♻️ 优化Tokens")

    btn_submit.click(submit_message, [input_message, state], [input_message, chatbot, state])
    input_message.submit(submit_message, [input_message, state], [input_message, chatbot, state])
    retry_conversation.click(retry, [state], [input_message, chatbot, state])
    btn_clear_conversation.click(clear_conversation, [], [input_message, chatbot, state])
    reduce_token_conversation.click(reduce_token, [state], [input_message, chatbot, state])


demo.launch(server_name="0.0.0.0",server_port=6000, debug=True)