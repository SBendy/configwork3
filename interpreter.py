#!/usr/bin/env python3
import struct

class UVMInterpreter:
    def __init__(self, memory_size=2048):  # Увеличим размер памяти
        self.memory = [0] * memory_size
        self.accumulator = 0
        self.pc = 0  # Program counter
        self.halted = False
        
    def load_program(self, binary_data):
        """Загрузка бинарной программы в память"""
        if len(binary_data) % 5 != 0:
            raise ValueError("Некорректный размер программы")
        
        # Очищаем память и аккумулятор
        self.memory = [0] * len(self.memory)
        self.accumulator = 0
        self.pc = 0
        self.halted = False
        
        # Загружаем программу в начало памяти
        program_size = len(binary_data)
        for i in range(0, program_size, 5):
            if i//5 < len(self.memory):
                self.memory[i//5] = int.from_bytes(binary_data[i:i+5], 'little')
    
    def decode_command(self, command):
        """Декодирование команды из 5 байт"""
        command_bytes = command.to_bytes(5, 'little')
        byte0, rest = struct.unpack('<BI', command_bytes)
        
        opcode = byte0 & 0x3F
        operand_low = (byte0 >> 6) & 0x3
        operand = (rest << 2) | operand_low
        
        return opcode, operand
    
    def execute_step(self):
        """Выполнение одной команды"""
        if self.halted or self.pc >= len(self.memory):
            return False
        
        command = self.memory[self.pc]
        if command == 0:  # Пустая команда
            return False
        
        opcode, operand = self.decode_command(command)
        
        # Выполнение команды
        try:
            if opcode == 58:  # LOAD_CONST
                # Преобразуем из 17-битного дополнительного кода
                if operand & 0x10000:  # Если отрицательное
                    operand = operand - (1 << 17)
                self.accumulator = operand
                
            elif opcode == 19:  # LOAD_MEM
                if operand >= len(self.memory):
                    raise MemoryError(f"Выход за границы памяти: {operand}")
                self.accumulator = self.memory[operand]
                
            elif opcode == 24:  # STORE_MEM
                if operand >= len(self.memory):
                    raise MemoryError(f"Выход за границы памяти: {operand}")
                self.memory[operand] = self.accumulator
                
            elif opcode == 7:  # ABS
                self.accumulator = abs(self.accumulator)
                if operand >= len(self.memory):
                    raise MemoryError(f"Выход за границы памяти: {operand}")
                self.memory[operand] = self.accumulator
                
            else:
                raise ValueError(f"Неизвестный код операции: {opcode}")
            
            self.pc += 1
            return True
            
        except Exception as e:
            print(f"Ошибка выполнения команды: {e}")
            self.halted = True
            return False
    
    def run(self):
        """Выполнение программы до завершения"""
        while self.execute_step():
            pass
    
    def get_state(self):
        """Получение текущего состояния виртуальной машины"""
        return {
            'accumulator': self.accumulator,
            'pc': self.pc,
            'memory': self.memory.copy(),  # Возвращаем копию всей памяти
            'halted': self.halted
        }
    
    def get_memory_cell(self, address):
        """Безопасное получение значения ячейки памяти"""
        if 0 <= address < len(self.memory):
            return self.memory[address]
        else:
            return None


def main():
    import sys
    
    if len(sys.argv) != 2:
        print("Использование: python interpreter.py <бинарный_файл>")
        sys.exit(1)
    
    binary_file = sys.argv[1]
    
    try:
        # Загрузка бинарной программы
        with open(binary_file, 'rb') as f:
            binary_data = f.read()
        
        # Создание и запуск интерпретатора
        interpreter = UVMInterpreter()
        interpreter.load_program(binary_data)
        
        print("Запуск программы...")
        interpreter.run()
        
        # Вывод состояния после выполнения
        state = interpreter.get_state()
        print(f"Аккумулятор: {state['accumulator']}")
        print(f"Счетчик команд: {state['pc']}")
        print(f"Статус: {'Остановлена' if state['halted'] else 'Завершена'}")
        print("Первые 20 ячеек памяти:")
        for i in range(20):
            print(f"  Memory[{i:3}]: {state['memory'][i]}")
            
    except Exception as e:
        print(f"Ошибка выполнения: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()