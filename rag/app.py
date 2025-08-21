
from flask import Flask, request, jsonify, render_template_string
from query import answer_with_guardrails

app = Flask(__name__)

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '')
    if not question:
        return jsonify({"error": "Question not provided"}), 400
    
    result = answer_with_guardrails(question)
    return jsonify(result)

@app.route('/')
def home():
    # Simple HTML + JavaScript frontend for asking questions in browser
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>BYD Seal Q&A</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            input[type="text"] { width: 400px; padding: 8px; font-size: 16px; }
            button { padding: 8px 16px; font-size: 16px; margin-left: 10px; }
            pre { white-space: pre-wrap; margin-top: 20px; border: 1px solid #ccc; padding: 10px; max-width: 600px; }
        </style>
    </head>
    <body>
        <h1>Ask a question about BYD Seal</h1>
        <input type="text" id="question" placeholder="Type your question here" autocomplete="off">
        <button onclick="ask()">Ask</button>
        <pre id="response"></pre>

        <script>
            async function ask() {
                const question = document.getElementById('question').value;
                const responseElem = document.getElementById('response');

                if (!question.trim()) {
                    responseElem.textContent = "Please enter a question.";
                    return;
                }

                responseElem.textContent = "Loading...";
                try {
                    const res = await fetch('/ask', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({question})
                    });
                    const data = await res.json();
                    responseElem.textContent = JSON.stringify(data, null, 2);
                } catch (error) {
                    responseElem.textContent = "Error: " + error.message;
                }
            }
        </script>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
