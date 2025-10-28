# Исправление поведения оператора Compare

## 🎯 Проблема
После нажатия кнопки "Compare" фокус переключался с оригинального объекта на созданный объект сравнения, что было неудобно для пользователя.

## ✅ Решение
Исправлен оператор `DFM_CompareVersionsOperator` в файле `classes/operators/version_operators.py`:

### Изменения в методе `execute()`:

1. **Сохранение ссылки на оригинальный объект ДО создания сравнения**:
   ```python
   # Store reference to original object BEFORE creating comparison
   original_obj = context.active_object
   original_obj_name = original_obj.name if original_obj else None
   ```

2. **Восстановление фокуса после создания объекта сравнения**:
   ```python
   # IMPORTANT: Restore focus to original object
   if original_obj and original_obj_name in bpy.data.objects:
       # Deselect all objects
       for obj in context.selected_objects:
           obj.select_set(False)
       
       # Select and activate the original object
       original_obj.select_set(True)
       context.view_layer.objects.active = original_obj
   ```

### Улучшения в методе `_remove_comparison_object()`:

Добавлено предупреждение, если оригинальный объект не найден:
```python
else:
    logger.warning(f"Original object '{original_name}' not found, keeping current selection")
```

## 🎯 Результат

Теперь после нажатия "Compare":
- ✅ Создается объект сравнения с суффиксом "_compare"
- ✅ Объект сравнения смещается на заданное расстояние
- ✅ **Фокус остается на оригинальном объекте**
- ✅ При отключении сравнения фокус также возвращается к оригинальному объекту

## 📝 Логирование

Добавлено подробное логирование для отладки:
- `"Restored focus to original object: {original_obj_name}"`
- `"Switched back to original object: {original_name}"`
- `"Original object '{original_name}' not found, keeping current selection"`

Поведение теперь соответствует ожиданиям пользователя - оригинальный объект остается активным для дальнейшего редактирования.
