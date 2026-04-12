class SearchFormMixin:
    def get_search_queryset(self, queryset):
        self.full_clean()
        for field in self.fields:
            value = self.cleaned_data.get(field)
            resolver = self.__resolvers__.get(field)
            if resolver and value:
                filter = resolver(value)
                if not filter:
                    continue

                if hasattr(filter, '__iter__'):
                    for expression in filter:
                        queryset = queryset.filter(expression)
                else:
                    queryset = queryset.filter(filter)

        return queryset