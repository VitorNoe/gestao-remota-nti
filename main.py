import redis
from tkinter import *
from tkinter import ttk, messagebox

class AppCRUD:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestão de Funcionários com Redis")
        self.id_selecionado = None
        
        # Conexão com Redis
        try:
            self.redis = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            self.redis.ping()  # Testa a conexão
        except redis.ConnectionError:
            messagebox.showerror("Erro", "Falha ao conectar ao Redis!")
            root.destroy()
            return

        self.criar_interface()
        self.inicializar_dados()

    def criar_interface(self):
        # Frame do formulário
        self.frame_form = Frame(self.root, padx=10, pady=10)
        self.frame_form.pack()

        # Campos do formulário
        campos = [
            ('Nome:', 'nome_entry'),
            ('CPF:', 'cpf_entry'),
            ('Cargo:', 'cargo_entry'),
            ('Departamento:', 'departamento_entry')
        ]

        for i, (label, entry) in enumerate(campos):
            Label(self.frame_form, text=label).grid(row=i, column=0, sticky=W)
            setattr(self, entry, Entry(self.frame_form, width=30))
            getattr(self, entry).grid(row=i, column=1)

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
        dados = {
            'nome': self.nome_entry.get(),
            'cpf': self.cpf_entry.get(),
            'cargo': self.cargo_entry.get(),
            'departamento': self.departamento_entry.get()
        }

        if not dados['nome'] or not dados['cpf']:
            messagebox.showwarning("Aviso", "Nome e CPF são obrigatórios!")
            return

        try:
            if self.id_selecionado:
                # Atualizar existente
                chave = f'funcionario:{self.id_selecionado}'
                if self.redis.hget(chave, 'cpf') != dados['cpf']:
                    if self.verificar_cpf_existente(dados['cpf']):
                        messagebox.showerror("Erro", "CPF já cadastrado!")
                        return
                self.redis.hset(chave, mapping=dados)
            else:
                # Criar novo
                if self.verificar_cpf_existente(dados['cpf']):
                    messagebox.showerror("Erro", "CPF já cadastrado!")
                    return
                novo_id = self.redis.incr('funcionario:id')
                chave = f'funcionario:{novo_id}'
                self.redis.hset(chave, mapping=dados)
            
            messagebox.showinfo("Sucesso", "Dados salvos com sucesso!")
            self.carregar_dados()
            self.limpar_formulario()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar: {e}")

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
                # Remove funcionário
                self.redis.delete(f'funcionario:{self.id_selecionado}')
                # Remove folhas de pagamento associadas
                for chave in self.redis.scan_iter(f'folha:{self.id_selecionado}:*'):
                    self.redis.delete(chave)
                messagebox.showinfo("Sucesso", "Registro excluído com sucesso!")
                self.carregar_dados()
                self.limpar_formulario()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao excluir: {e}")

    def verificar_cpf_existente(self, cpf):
        for chave in self.redis.scan_iter('funcionario:*'):
            if self.redis.hget(chave, 'cpf') == cpf:
                return True
        return False

    def preencher_formulario(self, event):
        selecionado = self.tree.selection()
        if not selecionado:
            return
            
        item = self.tree.item(selecionado[0])
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
            
        for chave in self.redis.scan_iter('funcionario:*'):
            funcionario_id = chave.split(':')[1]
            dados = self.redis.hgetall(chave)
            self.tree.insert('', 'end', values=(
                funcionario_id,
                dados['nome'],
                dados['cpf'],
                dados['cargo'],
                dados['departamento']
            ))

    def limpar_formulario(self):
        self.id_selecionado = None
        for entry in [self.nome_entry, self.cpf_entry, 
                     self.cargo_entry, self.departamento_entry]:
            entry.delete(0, END)

    def inicializar_dados(self):
        # Cria ID inicial se não existir
        if not self.redis.exists('funcionario:id'):
            self.redis.set('funcionario:id', 4)  # Considerando 4 registros iniciais

        # Dados iniciais
        funcionarios = [
            {'nome': 'Ana Silva', 'cpf': '123.456.789-00', 
             'cargo': 'Desenvolvedor', 'departamento': 'TI'},
            {'nome': 'Carlos Souza', 'cpf': '987.654.321-00', 
             'cargo': 'Gerente', 'departamento': 'RH'},
            {'nome': 'Maria Oliveira', 'cpf': '111.222.333-44', 
             'cargo': 'Designer', 'departamento': 'Marketing'},
            {'nome': 'João Santos', 'cpf': '555.666.777-88', 
             'cargo': 'Analista', 'departamento': 'Financeiro'}
        ]

        # Inserir dados iniciais se não existirem
        for i, func in enumerate(funcionarios, 1):
            chave = f'funcionario:{i}'
            if not self.redis.exists(chave):
                self.redis.hset(chave, mapping=func)
                # Inserir folha de pagamento
                self.redis.hset(f'folha:{i}:2024-05-01', mapping={
                    'mes_ano': '2024-05-01',
                    'horas_trabalhadas': 160,
                    'valor_pago': 5000.00 + (i * 1000)
                })

        # Inserir 4 registros adicionais
        funcionarios_adicionais = [
            {'nome': 'Pedro Costa', 'cpf': '999.888.777-66', 
             'cargo': 'Analista', 'departamento': 'TI'},
            {'nome': 'Julia Pereira', 'cpf': '444.333.222-11', 
             'cargo': 'Gerente', 'departamento': 'Vendas'},
            {'nome': 'Luiza Fernandes', 'cpf': '777.888.999-00', 
             'cargo': 'Designer', 'departamento': 'Marketing'},
            {'nome': 'Ricardo Almeida', 'cpf': '222.111.000-99', 
             'cargo': 'Diretor', 'departamento': 'Administração'}
        ]

        for func in funcionarios_adicionais:
            if not self.verificar_cpf_existente(func['cpf']):
                novo_id = self.redis.incr('funcionario:id')
                self.redis.hset(f'funcionario:{novo_id}', mapping=func)
                self.redis.hset(f'folha:{novo_id}:2024-05-01', mapping={
                    'mes_ano': '2024-05-01',
                    'horas_trabalhadas': 160,
                    'valor_pago': 7500.00 + (novo_id * 500)
                })

if __name__ == "__main__":
    root = Tk()
    app = AppCRUD(root)
    root.mainloop()
