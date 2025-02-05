import mysql.connector
from tkinter import *
from tkinter import ttk, messagebox

class AppCRUD:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestão de Funcionários Remota")
        self.conexao = mysql.connector.connect(
            host='db4free.net',
            user='vitornoe',
            password='arca0715',
            database='gestao_pessoal_remoto'
        )
        self.cursor = self.conexao.cursor()
        self.id_selecionado = None
        self.criar_interface()
        self.inserir_dados_adicionais()

    def criar_interface(self):
        # Frame do formulário
        self.frame_form = Frame(self.root, padx=10, pady=10)
        self.frame_form.pack()

        # Campos do formulário
        Label(self.frame_form, text="Nome:").grid(row=0, column=0, sticky=W)
        self.nome_entry = Entry(self.frame_form, width=30)
        self.nome_entry.grid(row=0, column=1)

        Label(self.frame_form, text="CPF:").grid(row=1, column=0, sticky=W)
        self.cpf_entry = Entry(self.frame_form, width=30)
        self.cpf_entry.grid(row=1, column=1)

        Label(self.frame_form, text="Cargo:").grid(row=2, column=0, sticky=W)
        self.cargo_entry = Entry(self.frame_form, width=30)
        self.cargo_entry.grid(row=2, column=1)

        Label(self.frame_form, text="Departamento:").grid(row=3, column=0, sticky=W)
        self.departamento_entry = Entry(self.frame_form, width=30)
        self.departamento_entry.grid(row=3, column=1)

        # Botões
        btn_frame = Frame(self.root, padx=10, pady=10)
        btn_frame.pack()
        
        Button(btn_frame, text="Salvar", command=self.salvar).grid(row=0, column=0, padx=5)
        Button(btn_frame, text="Editar", command=self.editar).grid(row=0, column=1, padx=5)
        Button(btn_frame, text="Excluir", command=self.excluir).grid(row=0, column=2, padx=5)
        Button(btn_frame, text="Limpar", command=self.limpar_formulario).grid(row=0, column=3, padx=5)

        # Treeview
        self.tree = ttk.Treeview(self.root, columns=('Nome', 'CPF', 'Cargo', 'Departamento'), show='headings')
        self.tree.heading('Nome', text='Nome')
        self.tree.heading('CPF', text='CPF')
        self.tree.heading('Cargo', text='Cargo')
        self.tree.heading('Departamento', text='Departamento')
        self.tree.column('Nome', width=150)
        self.tree.column('CPF', width=100)
        self.tree.column('Cargo', width=100)
        self.tree.column('Departamento', width=150)
        self.tree.pack(padx=10, pady=10, fill=BOTH, expand=True)
        
        self.tree.bind('<<TreeviewSelect>>', self.preencher_formulario)
        self.carregar_dados()

    def salvar(self):
        nome = self.nome_entry.get()
        cpf = self.cpf_entry.get()
        cargo = self.cargo_entry.get()
        departamento = self.departamento_entry.get()

        if not nome or not cpf:
            messagebox.showwarning("Aviso", "Nome e CPF são obrigatórios!")
            return

        try:
            if self.id_selecionado:
                self.cursor.execute(
                    "UPDATE Funcionarios SET nome=%s, cpf=%s, cargo=%s, departamento=%s WHERE id=%s",
                    (nome, cpf, cargo, departamento, self.id_selecionado)
                )
            else:
                self.cursor.execute(
                    "INSERT INTO Funcionarios (nome, cpf, cargo, departamento) VALUES (%s, %s, %s, %s)",
                    (nome, cpf, cargo, departamento)
                )
            
            self.conexao.commit()
            messagebox.showinfo("Sucesso", "Dados salvos com sucesso!")
            self.carregar_dados()
            self.limpar_formulario()
        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro ao salvar: {err}")

    def editar(self):
        if not self.id_selecionado:
            messagebox.showwarning("Aviso", "Selecione um registro para editar!")
            return
        self.salvar()

    def excluir(self):
        if not self.id_selecionado:
            messagebox.showwarning("Aviso", "Selecione um registro para excluir!")
            return
            
        if messagebox.askyesno("Confirmar", "Tem certeza que deseja excluir este registro?"):
            try:
                self.cursor.execute("DELETE FROM Funcionarios WHERE id=%s", (self.id_selecionado,))
                self.conexao.commit()
                messagebox.showinfo("Sucesso", "Registro excluído com sucesso!")
                self.carregar_dados()
                self.limpar_formulario()
            except mysql.connector.Error as err:
                messagebox.showerror("Erro", f"Erro ao excluir: {err}")

    def preencher_formulario(self, event):
        selected = self.tree.selection()
        if not selected:
            return
            
        item = self.tree.item(selected[0])
        self.id_selecionado = item['values'][0]
        self.nome_entry.delete(0, END)
        self.nome_entry.insert(0, item['values'][1])
        self.cpf_entry.delete(0, END)
        self.cpf_entry.insert(0, item['values'][2])
        self.cargo_entry.delete(0, END)
        self.cargo_entry.insert(0, item['values'][3])
        self.departamento_entry.delete(0, END)
        self.departamento_entry.insert(0, item['values'][4])

    def carregar_dados(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.cursor.execute("SELECT id, nome, cpf, cargo, departamento FROM Funcionarios")
        for row in self.cursor.fetchall():
            self.tree.insert('', 'end', values=row)

    def limpar_formulario(self):
        self.id_selecionado = None
        self.nome_entry.delete(0, END)
        self.cpf_entry.delete(0, END)
        self.cargo_entry.delete(0, END)
        self.departamento_entry.delete(0, END)

    def inserir_dados_adicionais(self):
        # Inserir 4 funcionários adicionais
        funcionarios_adicionais = [
            ('Pedro Costa', '999.888.777-66', 'Analista', 'TI'),
            ('Julia Pereira', '444.333.222-11', 'Gerente', 'Vendas'),
            ('Luiza Fernandes', '777.888.999-00', 'Designer', 'Marketing'),
            ('Ricardo Almeida', '222.111.000-99', 'Diretor', 'Administração')
        ]
        
        try:
            self.cursor.executemany(
                "INSERT INTO Funcionarios (nome, cpf, cargo, departamento) VALUES (%s, %s, %s, %s)",
                funcionarios_adicionais
            )
            
            # Inserir 4 folhas de pagamento adicionais
            folha_adicional = [
                (5, '2024-05-01', 160, 5500.00),
                (6, '2024-05-01', 160, 8500.00),
                (7, '2024-05-01', 120, 3200.00),
                (8, '2024-05-01', 160, 9000.00)
            ]
            
            self.cursor.executemany(
                "INSERT INTO Folha_Pagamento (funcionario_id, mes_ano, horas_trabalhadas, valor_pago) VALUES (%s, %s, %s, %s)",
                folha_adicional
            )
            
            self.conexao.commit()
        except mysql.connector.Error as err:
            print(f"Dados já existentes: {err}")

if __name__ == "__main__":
    root = Tk()
    app = AppCRUD(root)
    root.mainloop()
