;;; Directory Local Variables
;;; See Info node `(emacs) Directory Variables' for more information.

((python-mode
  (eval . (setq flycheck-flake8rc (expand-file-name ".flake8rc" (projectile-project-root))))))
