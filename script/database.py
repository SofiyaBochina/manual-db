class Database:
    def __init__(self):
        self.data = {"data": {}, "data_info": {}}
        self.transactions = []
        self.actual_data_location = {"data": {}, "data_info": {}}
        self.in_transaction = False

    def __get_actual_data(self, key, type):
        """
        Возвращает словарь с данными, гед находится актуальное значение ключа
        """
        if self.in_transaction:
            tr = self.actual_data_location[type].get(key)
            if tr:
                tr_id = tr[-1]
                return self.transactions[tr_id][type]
        return self.data[type]

    def __set_data_location(self, key, type):
        """
        Записывает ID текущей транзакции как последнее местоположение данных ключа
        """
        tr_id = len(self.transactions) - 1
        data = self.actual_data_location[type]
        if data.get(key) != tr_id:
            data.setdefault(key, []).append(tr_id)

    def __get_data_to_change(self, type):
        """
        Возвращает словарь с данными, где нужно произвести изменение
        """
        if self.in_transaction:
            return self.transactions[-1][type]
        return self.data[type]

    def __set_value_info(self, key, value):
        """
        Записывает данные о значении в data_info
        """
        data_info = self.__get_actual_data(value, "data_info")
        to_change = self.__get_data_to_change("data_info")

        actual_data = data_info.get(value, set())
        if actual_data == "NULL":
            to_change[value] = set()
        else:
            to_change[value] = actual_data.copy()
        to_change[value].add(key)
        if self.in_transaction:
            self.__set_data_location(value, "data_info")

    def __unset_value_info(self, key, value):
        """
        Удаляет данные о значении в data_info
        """
        data_info = self.__get_actual_data(value, "data_info")
        to_change = self.__get_data_to_change("data_info")

        actual_data = data_info[value]
        if len(actual_data) == 1:
            if self.in_transaction:
                to_change[value] = "NULL"
            else:
                del to_change[value]
        else:
            to_change[value] = actual_data.copy()
            to_change[value].remove(key)
        if self.in_transaction:
            self.__set_data_location(value, "data_info")

    def get(self, key):
        """
        Возвращает значение по ключу из data
        """
        data = self.__get_actual_data(key, "data")
        return data.get(key, "NULL")

    def set(self, key, value, data=None, to_change=None):
        """
        Записывает значение по ключу в data
        """
        data = self.__get_actual_data(key, "data")
        to_change = self.__get_data_to_change("data")

        current_value = data.get(key)
        if current_value == value:
            return
        if current_value and current_value != "NULL":
            self.__unset_value_info(key, current_value)
        to_change[key] = value
        self.__set_value_info(key, value)
        if self.in_transaction:
            self.__set_data_location(key, "data")

    def unset(self, key):
        """
        Удалет ключ вместе со значением в data
        """
        data = self.__get_actual_data(key, "data")
        to_change = self.__get_data_to_change("data")

        row = data.get(key)
        if row:
            self.__unset_value_info(key, row)
            if self.in_transaction:
                to_change[key] = "NULL"
                self.__set_data_location(key, "data")
            else:
                del to_change[key]
        else:
            return "NO SUCH DATA"

    def find(self, value):
        """
        Возвращает ключи по значению из data_info
        """
        data_info = self.__get_actual_data(value, "data_info")
        return data_info.get(value, "NULL")

    def counts(self, value):
        """
        Возвращает количество ключей по значению из data_info
        """
        data_info = self.__get_actual_data(value, "data_info")
        res = data_info.get(value, {})
        if res == "NULL":
            return 0
        return len(data_info.get(value, {}))

    def begin(self):
        """
        Задаёт начальное состояние транзакции
        """
        self.transactions.append({"data": {}, "data_info": {}})
        self.in_transaction = True

    def __clear_transcation_memory(self, tr_id):
        """
        Очищает данные транзакции и удаляет её
        """
        if tr_id == 0:
            self.in_transaction = False
            self.transactions = []
            self.actual_data_location = {"data": {}, "data_info": {}}
            return
        self.transactions.pop()
        for type in ("data", "data_info"):
            data_loc = self.actual_data_location[type]
            for key in list(data_loc.keys()):
                value = data_loc[key]
                if value[-1] == tr_id:
                    value.pop()
                if value == []:
                    del data_loc[key]

    def rollback(self):
        """
        Откатывает транзакцию
        """
        if not self.in_transaction:
            return "NO CURRENT TRANSACTION"
        tr_id = len(self.transactions) - 1
        self.__clear_transcation_memory(tr_id)

    def commit(self):
        """
        Коммитит транзакцию, записывает данные в предыдущее местоположение, обновляет местоположение
        """
        if not self.in_transaction:
            return "NO CURRENT TRANSACTION"
        tr_id = len(self.transactions) - 1
        if tr_id == 0:
            to_change = self.data
        else:
            to_change = self.transactions[-2]
        data = self.transactions[-1]

        for type in ("data", "data_info"):
            for key, value in data[type].items():
                if value == "NULL" and tr_id == 0 and to_change[type].get(key):
                    del to_change[type][key]
                elif tr_id != 0 or value != "NULL":
                    to_change[type][key] = value
                if tr_id != 0:
                    data_loc = self.actual_data_location[type][key]
                    if len(data_loc) < 2 or data_loc[-2] != tr_id - 1:
                        data_loc[-1] = tr_id - 1
                        self.__set_data_location(key, type)
        self.__clear_transcation_memory(tr_id)
