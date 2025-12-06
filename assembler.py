#!/usr/bin/env python3
import json
import sys
import struct

class UVMAssembler:
    # Коды операций
    OPCODES = {
        'LOAD_CONST': 58,
        'LOAD_MEM': 19,
        'STORE_MEM': 24,
        'ABS': 7
    }
    
    def __init__(self):
        self.program = []
    
    def parse_program(self, json_data):
        """Разбор JSON программы во внутреннее представление"""
        try:
            commands = json.loads(json_data)
            internal_repr = []
            
            for cmd in commands:
                opcode = cmd['opcode']
                operand = cmd['operand']
                
                if opcode not in self.OPCODES:
                    raise ValueError(f"Неизвестная операция: {opcode}")
                
                # Проверяем диапазоны операндов в зависимости от операции
                if opcode == 'LOAD_CONST':
                    # Для LOAD_CONST operand занимает 17 бит (0-131071)
                    if not isinstance(operand, int):
                        raise ValueError(f"Операнд должен быть целым числом: {operand}")
                    if operand < -0x10000 or operand > 0x1FFFF:
                        raise ValueError(f"Константа вне диапазона: {operand}")
                    # Преобразуем отрицательные числа в дополнительный код
                    if operand < 0:
                        operand = (1 << 17) + operand  # 17-битное представление
                else:
                    # Для остальных команд operand - адрес (31 бит, неотрицательный)
                    if not isinstance(operand, int) or operand < 0:
                        raise ValueError(f"Адрес должен быть неотрицательным целым: {operand}")
                    if operand > 0x7FFFFFFF:
                        raise ValueError(f"Адрес слишком большой: {operand}")
                
                internal_repr.append({
                    'opcode': opcode,
                    'opcode_num': self.OPCODES[opcode],
                    'operand': operand
                })
            
            return internal_repr
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка разбора JSON: {e}")
        except KeyError as e:
            raise ValueError(f"Отсутствует обязательное поле: {e}")
    
    def assemble_to_bytes(self, internal_repr):
        """Трансляция внутреннего представления в бинарный формат"""
        binary_data = b''
        
        for cmd in internal_repr:
            opcode = cmd['opcode_num']
            operand = cmd['operand']
            
            # Формируем 5-байтовую команду
            if cmd['opcode'] == 'LOAD_CONST':
                # Для LOAD_CONST operand занимает биты 6-22 (17 бит)
                if operand > 0x1FFFF:  # 131071
                    # Для отрицательных чисел в дополнительном коде
                    operand = operand & 0x1FFFF
                byte0 = opcode | ((operand & 0x3) << 6)
                rest = operand >> 2
            else:
                # Для остальных команд operand занимает биты 6-36 (31 бит)
                byte0 = opcode | ((operand & 0x3) << 6)
                rest = operand >> 2
            
            # Упаковываем в 5 байт (little-endian)
            command_bytes = struct.pack('<BI', byte0, rest)
            binary_data += command_bytes
        
        return binary_data
    
    def disassemble_command(self, command_bytes):
        """Дизассемблирование одной команды"""
        if len(command_bytes) != 5:
            raise ValueError("Команда должна быть длиной 5 байт")
        
        byte0, rest = struct.unpack('<BI', command_bytes)
        
        opcode_num = byte0 & 0x3F  # Младшие 6 бит
        operand_low = (byte0 >> 6) & 0x3  # 2 бита
        operand = (rest << 2) | operand_low
        
        # Для LOAD_CONST преобразуем из дополнительного кода если нужно
        if opcode_num == 58:  # LOAD_CONST
            if operand & 0x10000:  # Если старший бит установлен (отрицательное)
                operand = operand - (1 << 17)  # Преобразуем в знаковое
        
        # Находим мнемонику по коду
        opcode_name = None
        for name, code in self.OPCODES.items():
            if code == opcode_num:
                opcode_name = name
                break
        
        if opcode_name is None:
            opcode_name = f"UNKNOWN_{opcode_num}"
        
        return {
            'opcode': opcode_name,
            'opcode_num': opcode_num,
            'operand': operand
        }


def main():
    if len(sys.argv) < 3:
        print("Использование: python assembler.py <входной_файл> <выходной_файл> [--test]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    test_mode = len(sys.argv) > 3 and sys.argv[3] == '--test'
    
    assembler = UVMAssembler()
    
    try:
        # Чтение исходного файла
        with open(input_file, 'r', encoding='utf-8') as f:
            json_data = f.read()
        
        # Разбор программы
        internal_repr = assembler.parse_program(json_data)
        
        # Вывод внутреннего представления в режиме тестирования
        if test_mode:
            print("Внутреннее представление программы:")
            for i, cmd in enumerate(internal_repr):
                print(f"Команда {i}: {cmd}")
        
        # Трансляция в бинарный формат
        binary_data = assembler.assemble_to_bytes(internal_repr)
        
        # Сохранение результата
        with open(output_file, 'wb') as f:
            f.write(binary_data)
        
        print(f"Программа успешно ассемблирована в {output_file}")
        
        # Проверка тестовых случаев
        if test_mode:
            run_tests(assembler)
            
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)


def run_tests(assembler):
    """Запуск тестов из спецификации"""
    print("\n" + "="*50)
    print("ТЕСТИРОВАНИЕ КОМАНД ИЗ СПЕЦИФИКАЦИИ")
    print("="*50)
    
    test_cases = [
        # (имя, код операции, операнд, ожидаемые байты)
        ("LOAD_CONST 308", "LOAD_CONST", 308, bytes([0x3A, 0x4D, 0x00, 0x00, 0x00])),
        ("LOAD_MEM 705", "LOAD_MEM", 705, bytes([0x53, 0xB0, 0x00, 0x00, 0x00])),
        ("STORE_MEM 791", "STORE_MEM", 791, bytes([0xD8, 0xC5, 0x00, 0x00, 0x00])),
        ("ABS 870", "ABS", 870, bytes([0x87, 0xD9, 0x00, 0x00, 0x00])),
    ]
    
    # Тест с отрицательной константой
    negative_test = ("LOAD_CONST -15", "LOAD_CONST", -15, None)
    
    all_passed = True
    
    for test_name, opcode, operand, expected in test_cases:
        # Создаем тестовую программу
        test_program = [{'opcode': opcode, 'operand': operand}]
        json_data = json.dumps(test_program)
        
        try:
            # Ассемблируем
            internal_repr = assembler.parse_program(json_data)
            binary_data = assembler.assemble_to_bytes(internal_repr)
            
            # Проверяем результат
            if binary_data == expected:
                print(f"✓ {test_name}: PASS")
                hex_repr = ' '.join(f'0x{byte:02X}' for byte in binary_data)
                print(f"  Результат: [{hex_repr}]")
            else:
                print(f"✗ {test_name}: FAIL")
                expected_hex = ' '.join(f'0x{byte:02X}' for byte in expected)
                actual_hex = ' '.join(f'0x{byte:02X}' for byte in binary_data)
                print(f"  Ожидалось: [{expected_hex}]")
                print(f"  Получено:  [{actual_hex}]")
                all_passed = False
                
        except Exception as e:
            print(f"✗ {test_name}: ERROR - {e}")
            all_passed = False
    
    # Тестируем отрицательную константу
    print("\nТест отрицательной константы:")
    test_name, opcode, operand, _ = negative_test
    test_program = [{'opcode': opcode, 'operand': operand}]
    json_data = json.dumps(test_program)
    
    try:
        internal_repr = assembler.parse_program(json_data)
        binary_data = assembler.assemble_to_bytes(internal_repr)
        
        # Дизассемблируем обратно для проверки
        disassembled = assembler.disassemble_command(binary_data)
        
        if disassembled['operand'] == operand:
            print(f"✓ {test_name}: PASS")
            hex_repr = ' '.join(f'0x{byte:02X}' for byte in binary_data)
            print(f"  Результат: [{hex_repr}] -> {disassembled['operand']}")
        else:
            print(f"✗ {test_name}: FAIL")
            print(f"  Ожидалось: {operand}")
            print(f"  Получено:  {disassembled['operand']}")
            all_passed = False
            
    except Exception as e:
        print(f"✗ {test_name}: ERROR - {e}")
        all_passed = False
    
    print("="*50)
    if all_passed:
        print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ!")
    print("="*50)


if __name__ == '__main__':
    main()