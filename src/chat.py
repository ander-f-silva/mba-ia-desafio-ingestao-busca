from search import search_prompt

def main():
    while True:
        question = input("PERGUNTA: ").strip()
        if not question:
            break
        answer = search_prompt(question)
        print(f"RESPOSTA: {answer}\n")

if __name__ == "__main__":
    main()