# MCP Unit Converter with LLM Integration

```markdown
The **MCP Unit Converter** is a Python-based application that integrates the [MCP SDK](https://github.com/modelcontextprotocol) with the **Llama 3.1 8B** model (via [Ollama](https://ollama.com)) to perform **precise unit conversions** for length, mass, and temperature.  

The system follows a **client-server architecture**:
- **client.py** → Interacts with the user and the LLM.
- **server.py** → Handles conversion logic using the MCP `convert` tool.
- **units://supported_units.json** → Defines all supported units.

---

## ✨ Features

- **Unit Conversions**  
  - Length: `mm, cm, m, km, in, ft, yd, mi`  
  - Mass: `mg, g, kg, tonne, oz, lb`  
  - Temperature: `C, F, K`

- **LLM Integration**  
  Natural language input like:  
```

convert 100 cm to inches
convert 32 fahrenheit to celsius

```

- **MCP SDK**  
Uses MCP tools for precise calculations instead of relying only on the LLM.

- **Interactive CLI**  
Command-line interface with `exit` command to quit.

- **Precision Control**  
Default: 6 decimal places (configurable).

---

## 📂 Project Structure

```

````

---

## 🔧 Prerequisites

- **Python** ≥ 3.10  
- **Ollama** installed and running with **Llama 3.1 8B** model  
- **Operating System**: Windows/Linux/macOS  
- **Disk Space**: ~15GB free (Ollama model files + temp files)  
- **RAM**: 8GB (16GB recommended)  

---

## ⚙️ Installation

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/your-username/mcp-unit-converter-llm.git
   cd mcp-unit-converter-llm
````

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install Ollama**

   * Download Ollama from [ollama.com](https://ollama.com)
   * Pull the Llama 3.1 8B model:

     ```bash
     ollama pull llama3.1:8b
     ```

---

## 🚀 Usage

1. **Start Ollama Server**

   ```bash
   ollama serve
   ```

   Verify:

   ```bash
   curl http://127.0.0.1:11434
   ```

   Should return: `Ollama is running.`

2. **Run the Client**

   ```bash
   python client.py
   ```

3. **Example Queries**

   ```
   You: convert 100 cm to inches
   Assistant: The conversion of 100 cm to inches is 39.37 inches.
   ```

   ```
   You: convert 32 fahrenheit to celsius
   Assistant: The conversion of 32 Fahrenheit to Celsius is 0.0 °C.
   ```

   Type `exit` to quit.

---

## ⚙️ How It Works

* **Client (client.py)**

  * Starts the MCP server (`server.py`)
  * Retrieves supported units
  * Uses `ollama.chat` for LLM interaction
  * Handles tool calls (`convert`) and displays results

* **Server (server.py)**

  * Defines the `convert` tool
  * Uses conversion factors & formulas from `supported_units.json`
  * Serves resources via MCP

* **LLM Integration**

  * Llama 3.1 8B interprets queries
  * Calls the MCP tool when conversions are required

---

## 🧾 Supported Units

* **Length**: `mm, cm, m, km, in, ft, yd, mi`
* **Mass**: `mg, g, kg, tonne, oz, lb`
* **Temperature**: `Celsius (C), Fahrenheit (F), Kelvin (K)`

---

## 🛠 Troubleshooting

* **Ollama not running** → Run `ollama serve` and check port `11434`.
* **Low disk space** → Ensure at least 15GB free.
* **No tool calls** → Check `server.py` and ensure `convert` tool is correctly registered.
* **Slow performance** → Try smaller model:

  ```bash
  ollama pull llama3:8b
  ```

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit changes (`git commit -m "Add YourFeature"`)
4. Push (`git push origin feature/YourFeature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the **MIT License**.

---



Would you like me to also **generate a sample `requirements.txt`** (with exact package names like `mcp` and `ollama`) so your repo is fully ready-to-push?
```
