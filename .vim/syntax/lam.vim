syntax match LamVac /:/
syntax match LamVar /[^ 	:]*:\@=/
syntax match LamVal /[^ 	:]\+\($\|\s\)\@=/

hi def link LamVac Keyword
hi def link LamVar Identifier
hi def link LamVal String
