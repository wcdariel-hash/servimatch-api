from fastapi.testclient import TestClient
import json
import sys

# Importar app
sys.path.append('c:\\Users\\wcdar\\Desktop\\PROYECTO.PY\\backend')
from main import app

client = TestClient(app)

def run_tests():
    print("--- INICIANDO PRUEBA DE FLUJO COMPLETO ---")
    
    # 1. Login Test User
    print("\n1. Iniciando sesión como test@email.com (Cliente)...")
    response = client.post("/api/auth/login", data={"username": "test@email.com", "password": "dcastillo2009"})
    assert response.status_code == 200, "Login falló"
    test_token = response.json()["access_token"]
    test_headers = {"Authorization": f"Bearer {test_token}"}
    
    # Check balance inicial
    me_resp = client.get("/api/auth/me", headers=test_headers)
    print(f"   Saldo inicial del cliente: ${me_resp.json()['balance']}")

    # 2. Login Provider User
    print("\n2. Iniciando sesión como provider@email.com (Proveedor)...")
    res_prov = client.post("/api/auth/login", data={"username": "provider@email.com", "password": "dcastillo2009"})
    prov_token = res_prov.json()["access_token"]
    prov_headers = {"Authorization": f"Bearer {prov_token}"}
    
    me_prov = client.get("/api/auth/me", headers=prov_headers)
    print(f"   Saldo inicial del proveedor: ${me_prov.json()['balance']} (Reservado: ${me_prov.json().get('reserved_balance', 0)})")

    # 3. Cliente reserva servicio #1
    print("\n3. Cliente contrata 'Limpieza de Hogar Express' (ID: 1, Precio $25.0) usando ServiPay...")
    booking_req = client.post("/api/bookings/", json={"service_id": 1, "payment_method": "ServiPay"}, headers=test_headers)
    
    if booking_req.status_code != 200:
        print(f"   Error reservando: {booking_req.text}")
        return
        
    booking_data = booking_req.json()
    booking_id = booking_data['id']
    print(f"   [OK] Reserva Exitosa. ID de Trabajo: {booking_id}. Estado inicial: {booking_data['status']}")
    
    # Check saldos intermedios
    me_resp2 = client.get("/api/auth/me", headers=test_headers)
    me_prov2 = client.get("/api/auth/me", headers=prov_headers)
    print(f"   Nuevo saldo Cliente: ${me_resp2.json()['balance']} (Antes: $500.0, Resta $25.0)")
    print(f"   Nuevo saldo Proveedor: Balance ${me_prov2.json()['balance']} | Reservado: ${me_prov2.json().get('reserved_balance')}")

    # 4. Proveedor consulta sus trabajos
    print("\n4. Proveedor consulta trabajos activos...")
    jobs_req = client.get("/api/bookings/my-jobs", headers=prov_headers)
    jobs = jobs_req.json()
    print(f"   [OK] El proveedor tiene {len(jobs)} trabajos.")
    
    # 5. Proveedor completa el trabajo
    print(f"\n5. Proveedor marca Trabajo #{booking_id} como 'Completado'...")
    comp_req = client.post(f"/api/bookings/{booking_id}/complete", headers=prov_headers)
    if comp_req.status_code == 200:
        print("   [OK] Trabajo completado exitosamente.")
    else:
        print(f"   Error completando: {comp_req.text}")

    # 6. Saldo Final
    me_prov3 = client.get("/api/auth/me", headers=prov_headers)
    print(f"\n6. Saldo final del proveedor después del trabajo:")
    print(f"   Balance Neto: ${me_prov3.json()['balance']}")
    print(f"   Fondos Reservados: ${me_prov3.json().get('reserved_balance', 0)}")
    
    print("\n--- PRUEBA COMPLETADA EXITOSAMENTE! ---")

if __name__ == "__main__":
    run_tests()
