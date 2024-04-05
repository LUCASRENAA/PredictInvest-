import argparse
import subprocess


def formatar_data():
    import datetime

    data_atual = datetime.datetime.now()
    data_formatada = data_atual.strftime("%d-%m-%Y %H %M %S")
    #print("Data atual:", data_formatada)
    return data_formatada


def previsao_dividendos():
    subprocess.call(["python", "previsao_dividendos.py"])

def pegar_indicadores():
    subprocess.call(["python", "pegar_indicadores.py"])

def algoritmos():
    subprocess.call(["python", "algoritmos.py"])

def main():
    # Criação do parser de argumentos
    parser = argparse.ArgumentParser(
    description="Este programa oferece ferramentas para análise de investimentos, incluindo previsão de dividendos, coleta de indicadores financeiros e execução de algoritmos de avaliação de investimentos.",
    epilog="Para mais informações, consulte a documentação do programa ou entre em contato com o desenvolvedor."
)



    # Adiciona argumento para execução da previsão de dividendos
    parser.add_argument("--previsao_dividendos", "-pd", action="store_true", help="Executar a previsão de dividendos. Antes de executar esta opção, certifique-se de ter os seguintes arquivos: acoes.csv e/ou fiis.csv.")

    # Adiciona argumento para execução da coleta de indicadores
    parser.add_argument("--pegar_indicadores", "-pi", action="store_true", help="Coletar os indicadores das ações.")

    # Adiciona argumento para execução dos algoritmos de Bazin e Graham nos indicadores
    parser.add_argument("--algoritmos", "-pa", action="store_true", help="Executar algoritmos de Bazin e Graham nos indicadores coletados. Para Bazin foi utilizado essa formula (lpa*payout/100)/0.07, para Graham foi utilizado (12 * lpa * vpa) e para o metodo nathalia foi feito a média dos dois algoritmos anteriores")


    # Adiciona argumento para executar todas as opções
    parser.add_argument("--all", action="store_true", help="Executar todas as opções: previsão de dividendos, coleta de indicadores e execução dos algoritmos.")

    # Realiza o parsing dos argumentos da linha de comando
    args = parser.parse_args()

    # Verifica se a opção -all foi fornecida
    if args.all:
        print("Executando todas as opções...")
        print("Previsão de dividendos...\n\n")
        previsao_dividendos()
        print("Coletando indicadores...\n\n")

        pegar_indicadores()
        print("Realizando calculos...\n\n")
        algoritmos()
    else:
        # Verifica se o argumento de previsão de dividendos foi fornecido
        if args.previsao_dividendos:
            previsao_dividendos()
        elif args.pegar_indicadores:
            print("Coletando indicadores das ações...")
            pegar_indicadores()
        elif args.algoritmos:
            print("Executando algoritmos de Bazin e Graham nos indicadores...")
            algoritmos()

if __name__ == "__main__":
    

    main()
