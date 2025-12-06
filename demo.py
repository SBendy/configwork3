#!/usr/bin/env python3
# demo.py - Демонстрация работы ассемблера и интерпретатора

import json
from assembler import UVMAssembler
from interpreter import UVMInterpreter

def demo_basic():
    print("ДЕМОНСТРАЦИЯ АССЕМБЛЕРА И ИНТЕРПРЕТАТОРА УВМ")
    print("=" * 50)
    
    # Создаем тестовую программу
    test_program = [
        {"opcode": "LOAD_CONST", "operand": 42},
        {"opcode": "STORE_MEM", "operand": 100},
        {"opcode": "LOAD_CONST", "operand": 15},
        {"opcode": "ABS", "operand": 101},
        {"opcode": "LOAD_MEM", "operand": 100}
    ]
    
    print("Исходная программа:")
    print(json.dumps(test_program, indent=2, ensure_ascii=False))
    
    # Ассемблирование
    assembler = UVMAssembler()
    json_data = json.dumps(test_program)
    
    try:
        internal_repr = assembler.parse_program(json_data)
        binary_data = assembler.assemble_to_bytes(internal_repr)
        
        print("\nВнутреннее представление:")
        for i, cmd in enumerate(internal_repr):
            print(f"  {i}: {cmd}")
        
        print(f"\nБинарный размер: {len(binary_data)} байт")
        
        # Интерпретация
        interpreter = UVMInterpreter(memory_size=1024)  # Явно задаем размер памяти
        interpreter.load_program(binary_data)
        
        print("\nВыполнение программы:")
        step = 0
        while interpreter.execute_step():
            state = interpreter.get_state()
            print(f"Шаг {step}: ACC={state['accumulator']}, PC={state['pc']}")
            step += 1
        
        print("\nФинальное состояние:")
        state = interpreter.get_state()
        print(f"Аккумулятор: {state['accumulator']}")
        
        # Безопасное обращение к памяти
        mem_100 = interpreter.get_memory_cell(100)
        mem_101 = interpreter.get_memory_cell(101)
        print(f"Память[100]: {mem_100}")
        print(f"Память[101]: {mem_101}")
        
    except Exception as e:
        print(f"Ошибка: {e}")

def demo_accumulator_workflow():
    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯ РАБОТЫ АККУМУЛЯТОРА")
    print("="*50)
    
    # Программа, показывающая работу аккумулятора
    test_program = [
        {"opcode": "LOAD_CONST", "operand": 100},    # Аккумулятор = 100
        {"opcode": "STORE_MEM", "operand": 10},      # Память[10] = 100
        {"opcode": "LOAD_CONST", "operand": 50},     # Аккумулятор = 50  
        {"opcode": "STORE_MEM", "operand": 11},      # Память[11] = 50
        {"opcode": "LOAD_MEM", "operand": 10},       # Аккумулятор = 100
        {"opcode": "ABS", "operand": 12},            # Аккумулятор = 100, Память[12] = 100
    ]
    
    print("Программа:")
    for i, cmd in enumerate(test_program):
        print(f"  {i}: {cmd['opcode']} {cmd['operand']}")
    
    # Выполнение
    assembler = UVMAssembler()
    interpreter = UVMInterpreter(memory_size=1024)
    
    try:
        json_data = json.dumps(test_program)
        binary_data = assembler.assemble_to_bytes(assembler.parse_program(json_data))
        interpreter.load_program(binary_data)
        
        print("\nПошаговое выполнение:")
        print("ШАГ | КОМАНДА           | АККУМУЛЯТОР | ПАМЯТЬ[10] | ПАМЯТЬ[11] | ПАМЯТЬ[12]")
        print("-" * 80)
        
        step = 0
        while step < len(test_program) and interpreter.execute_step():
            state = interpreter.get_state()
            mem_10 = interpreter.get_memory_cell(10)
            mem_11 = interpreter.get_memory_cell(11) 
            mem_12 = interpreter.get_memory_cell(12)
            
            print(f"{step:3} | {test_program[step]['opcode']:15} {test_program[step]['operand']:3} | "
                  f"{state['accumulator']:11} | {mem_10:10} | {mem_11:10} | {mem_12:10}")
            step += 1
            
    except Exception as e:
        print(f"Ошибка: {e}")

def demo_negative_numbers():
    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯ РАБОТЫ С ОТРИЦАТЕЛЬНЫМИ ЧИСЛАМИ")
    print("="*50)
    
    program = [
        {"opcode": "LOAD_CONST", "operand": -25},   # Аккумулятор = -25
        {"opcode": "ABS", "operand": 30},           # Аккумулятор = 25, Память[30] = 25
        {"opcode": "STORE_MEM", "operand": 31},     # Память[31] = 25
        {"opcode": "LOAD_CONST", "operand": -100},  # Аккумулятор = -100
        {"opcode": "ABS", "operand": 32},           # Аккумулятор = 100, Память[32] = 100
    ]
    
    print("Программа:")
    for cmd in program:
        print(f"  {cmd['opcode']} {cmd['operand']}")
    
    assembler = UVMAssembler()
    interpreter = UVMInterpreter(memory_size=1024)
    
    try:
        json_data = json.dumps(program)
        binary_data = assembler.assemble_to_bytes(assembler.parse_program(json_data))
        interpreter.load_program(binary_data)
        
        print("\nВыполнение:")
        step = 0
        while step < len(program) and interpreter.execute_step():
            state = interpreter.get_state()
            cmd = program[step]
            print(f"Шаг {step}: {cmd['opcode']} {cmd['operand']}")
            print(f"  Аккумулятор: {state['accumulator']}")
            
            # Показываем relevant memory cells
            if step >= 1:  # После первой команды начинаем запись в память
                mem_30 = interpreter.get_memory_cell(30)
                mem_31 = interpreter.get_memory_cell(31)
                mem_32 = interpreter.get_memory_cell(32)
                print(f"  Память[30]: {mem_30}")
                print(f"  Память[31]: {mem_31}")
                print(f"  Память[32]: {mem_32}")
            print()
            step += 1
            
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == '__main__':
    demo_basic()
    demo_accumulator_workflow()
    demo_negative_numbers()