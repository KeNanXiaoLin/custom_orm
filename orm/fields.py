import datetime


class Field:
    def __init__(self, name=None, primary_key=False, nullable=True, default=None):
        self.name = name
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self._attr_name = None
    
    def __set_name__(self, owner, name):
        self._attr_name = name
        if self.name is None:
            self.name = name
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self._attr_name, self.default)
    
    def __set__(self, instance, value):
        if not self.nullable and value is None:
            raise ValueError(f"{self._attr_name} cannot be None")
        self.validate(value)
        instance.__dict__[self._attr_name] = value
    
    def validate(self, value):
        pass
    
    def db_type(self):
        raise NotImplementedError


class IntegerField(Field):
    def validate(self, value):
        if value is not None and not isinstance(value, int):
            raise ValueError(f"{self._attr_name} must be an integer")
    
    def db_type(self):
        return "INTEGER"


class StringField(Field):
    def __init__(self, name=None, primary_key=False, nullable=True, default=None, max_length=255):
        super().__init__(name, primary_key, nullable, default)
        self.max_length = max_length
    
    def validate(self, value):
        if value is not None:
            if not isinstance(value, str):
                raise ValueError(f"{self._attr_name} must be a string")
            if len(value) > self.max_length:
                raise ValueError(f"{self._attr_name} cannot exceed {self.max_length} characters")
    
    def db_type(self):
        return f"VARCHAR({self.max_length})"


class BooleanField(Field):
    def validate(self, value):
        if value is not None:
            if not isinstance(value, (bool, int)):
                raise ValueError(f"{self._attr_name} must be a boolean or integer")
            if isinstance(value, int) and value not in (0, 1):
                raise ValueError(f"{self._attr_name} must be 0, 1, True, or False")
    
    def __set__(self, instance, value):
        if not self.nullable and value is None:
            raise ValueError(f"{self._attr_name} cannot be None")
        self.validate(value)
        # Convert integer booleans to actual booleans
        if isinstance(value, int):
            value = bool(value)
        instance.__dict__[self._attr_name] = value
    
    def db_type(self):
        return "BOOLEAN"


class DateTimeField(Field):
    def __init__(self, name=None, primary_key=False, nullable=True, default=None, auto_now=False, auto_now_add=False):
        super().__init__(name, primary_key, nullable, default)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
    
    def validate(self, value):
        if value is not None and not isinstance(value, datetime.datetime):
            raise ValueError(f"{self._attr_name} must be a datetime object")
    
    def db_type(self):
        return "DATETIME"


class FloatField(Field):
    def validate(self, value):
        if value is not None and not isinstance(value, (int, float)):
            raise ValueError(f"{self._attr_name} must be a number")
    
    def db_type(self):
        return "FLOAT"
