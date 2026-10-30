from sdas.core.client.SDASClient import SDASClient

HOST = "baco.ipfn.tecnico.ulisboa.pt"
PORT = 8888
SHOT = 46241

client = SDASClient(HOST, PORT)

queries = [
    f"{SHOT}.cfg",
    f"#{SHOT}.cfg",
]

for q in queries:
    print(f"\n=== QUERY: {q} ===")

    try:
        r = client.searchParametersByName(q)
        print("searchParametersByName:", r)
    except Exception as e:
        print("searchParametersByName ERROR:", e)

    try:
        r = client.searchParametersByDescription(q)
        print("searchParametersByDescription:", r)
    except Exception as e:
        print("searchParametersByDescription ERROR:", e)

    try:
        r = client.searchDeclaredEventsByName(q)
        print("searchDeclaredEventsByName:", r)
    except Exception as e:
        print("searchDeclaredEventsByName ERROR:", e)

    try:
        r = client.searchDeclaredEventsByDescription(q)
        print("searchDeclaredEventsByDescription:", r)
    except Exception as e:
        print("searchDeclaredEventsByDescription ERROR:", e)
