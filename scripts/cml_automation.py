import getpass
import re
import pexpect

password = getpass.getpass("Password de CML: ")

ssh = pexpect.spawn(
    "ssh",
    ["-tt", "-o", "StrictHostKeyChecking=yes",
     "developer@10.10.20.161"],
    encoding="utf-8",
    timeout=60
)

prompt = r"(?m)^R1(?:\([^)]+\))?#[ \t]*$"

def ejecutar(comando):
    ssh.sendline(comando)
    ssh.expect_exact(comando)
    ssh.expect(prompt)
    salida = ssh.before.strip()
    print(comando)
    print(salida)
    if re.search(r"% (Invalid|Incomplete|Ambiguous)", salida):
        raise RuntimeError("Comando rechazado")
    return salida

try:
    ssh.expect("password:")
    ssh.sendline(password)
    ssh.expect_exact("consoles>")
    ssh.sendline("open /DEVOPS-MANAGER-LAB/R1-0/0")
    ssh.expect_exact("Escape character is '^]'.")
    ssh.sendline("")
    ssh.expect(prompt)

    ejecutar("terminal length 0")

    print("\n=== ESTADO INICIAL ===")
    ejecutar("show ip interface brief")

    anterior = ejecutar(
        "show running-config | section ^interface Loopback110$"
    )

    if re.search(r"(?m)^interface Loopback110", anterior):
        if "DEVOPS-MANAGER-CML" not in anterior:
            raise RuntimeError("Interfaz existente no autorizada")
    else:
        print("\n=== CONFIGURACION AUTOMATICA ===")
        ejecutar("configure terminal")
        ejecutar("interface Loopback110")
        ejecutar("description DEVOPS-MANAGER-CML")
        ejecutar("no shutdown")
        ejecutar("end")

    print("\n=== VALIDACION FINAL ===")
    resultado = ejecutar(
        "show running-config | section ^interface Loopback110$"
    )
    assert "DEVOPS-MANAGER-CML" in resultado

    ejecutar("show ip interface brief")
    ping = ejecutar("ping 10.10.10.2")
    assert "100 percent (5/5)" in ping

    ejecutar("write memory")

    print("\nCML: AUTOMATIZACION EXITOSA")
    print("CML: CONECTIVIDAD VALIDADA")

finally:
    ssh.close(force=True)
