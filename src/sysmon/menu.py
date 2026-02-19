"""
SysMon Menu Bar Mixin
Complete menu bar construction for the main window.
"""

from PyQt5.QtWidgets import QAction


class MenuMixin:
    """Menu bar construction methods for SystemMonitor."""

    def setup_menu_bar(self):
        """Setup the application menu bar"""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu('&File')

        save_data_action = QAction('&Save Data...', self)
        save_data_action.setShortcut('Ctrl+S')
        save_data_action.setStatusTip('Save monitoring data to file')
        save_data_action.triggered.connect(self.save_data)
        file_menu.addAction(save_data_action)

        export_graph_action = QAction('&Export Graph...', self)
        export_graph_action.setShortcut('Ctrl+E')
        export_graph_action.setStatusTip('Export graph as image')
        export_graph_action.triggered.connect(self.export_graph)
        file_menu.addAction(export_graph_action)

        file_menu.addSeparator()

        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menubar.addMenu('&Edit')

        copy_graph_action = QAction('&Copy Graph to Clipboard', self)
        copy_graph_action.setShortcut('Ctrl+C')
        copy_graph_action.setStatusTip('Copy current graph to clipboard')
        copy_graph_action.triggered.connect(self.copy_graph)
        edit_menu.addAction(copy_graph_action)

        clear_data_action = QAction('&Clear All Data', self)
        clear_data_action.setShortcut('Ctrl+Del')
        clear_data_action.setStatusTip('Clear all monitoring data')
        clear_data_action.triggered.connect(self.clear_data)
        edit_menu.addAction(clear_data_action)

        edit_menu.addSeparator()

        reset_settings_action = QAction('&Reset Settings', self)
        reset_settings_action.setStatusTip('Reset all settings to defaults')
        reset_settings_action.triggered.connect(self.reset_settings)
        edit_menu.addAction(reset_settings_action)

        # View Menu
        view_menu = menubar.addMenu('&View')

        self.show_cpu_action = QAction('Show &CPU', self, checkable=True)
        self.show_cpu_action.setChecked(True)
        self.show_cpu_action.triggered.connect(self.toggle_cpu_plot)
        view_menu.addAction(self.show_cpu_action)

        self.show_memory_action = QAction('Show &Memory', self, checkable=True)
        self.show_memory_action.setChecked(True)
        self.show_memory_action.triggered.connect(self.toggle_memory_plot)
        view_menu.addAction(self.show_memory_action)

        self.show_disk_action = QAction('Show &Disk I/O', self, checkable=True)
        self.show_disk_action.setChecked(True)
        self.show_disk_action.triggered.connect(self.toggle_disk_plot)
        view_menu.addAction(self.show_disk_action)

        self.show_network_action = QAction('Show &Network', self, checkable=True)
        self.show_network_action.setChecked(True)
        self.show_network_action.triggered.connect(self.toggle_network_plot)
        view_menu.addAction(self.show_network_action)

        view_menu.addSeparator()

        fullscreen_action = QAction('&Full Screen', self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.setStatusTip('Toggle full screen mode')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # Config Menu
        config_menu = menubar.addMenu('&Config')

        view_config_action = QAction('View Config &Files', self)
        view_config_action.setStatusTip('View SysMon configuration files')
        view_config_action.triggered.connect(self.view_config_files)
        config_menu.addAction(view_config_action)

        config_menu.addSeparator()

        update_interval_action = QAction('&Update Interval...', self)
        update_interval_action.setStatusTip('Change data update interval')
        update_interval_action.triggered.connect(self.change_update_interval)
        config_menu.addAction(update_interval_action)

        time_window_action = QAction('&Time Window Settings...', self)
        time_window_action.setStatusTip('Configure time window settings')
        time_window_action.triggered.connect(self.change_time_window_settings)
        config_menu.addAction(time_window_action)

        smoothing_action = QAction('&Smoothing Level...', self)
        smoothing_action.setStatusTip('Configure graph smoothing level')
        smoothing_action.triggered.connect(self.change_smoothing_level)
        config_menu.addAction(smoothing_action)

        theme_action = QAction('T&heme...', self)
        theme_action.setStatusTip('Select theme mode (Auto/Light/Dark)')
        theme_action.triggered.connect(self.change_theme)
        config_menu.addAction(theme_action)

        graph_colors_action = QAction('&Graph Colors...', self)
        graph_colors_action.setStatusTip('Customize graph colors')
        graph_colors_action.setShortcut('Ctrl+G')  # Add keyboard shortcut
        graph_colors_action.triggered.connect(self.customize_graph_colors)
        config_menu.addAction(graph_colors_action)

        line_thickness_action = QAction('Line &Thickness...', self)
        line_thickness_action.setStatusTip('Adjust graph line thickness')
        line_thickness_action.triggered.connect(self.customize_line_thickness)
        config_menu.addAction(line_thickness_action)

        config_menu.addSeparator()

        transparency_action = QAction('&Transparency...', self)
        transparency_action.setStatusTip('Set window transparency for see-through mode')
        transparency_action.triggered.connect(self.change_transparency)
        config_menu.addAction(transparency_action)

        self.always_on_top_action = QAction('&Always On Top', self, checkable=True)
        self.always_on_top_action.setStatusTip('Keep window always on top of other windows')
        self.always_on_top_action.triggered.connect(self.toggle_always_on_top)
        config_menu.addAction(self.always_on_top_action)

        # Help Menu
        help_menu = menubar.addMenu('&Help')

        changelog_action = QAction('&ChangeLog', self)
        changelog_action.setStatusTip('View SysMon development history and changes')
        changelog_action.triggered.connect(self.show_changelog)
        help_menu.addAction(changelog_action)

        changelog_github_action = QAction('ChangeLog (&GitHub)', self)
        changelog_github_action.setStatusTip('Open ChangeLog on GitHub in web browser')
        changelog_github_action.triggered.connect(self.show_changelog_github)
        help_menu.addAction(changelog_github_action)

        check_updates_action = QAction('Check for &Updates', self)
        check_updates_action.setStatusTip('Check for newer SysMon releases on GitHub')
        check_updates_action.setShortcut('F5')  # Add keyboard shortcut
        check_updates_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(check_updates_action)

        # Add update preferences to Config menu
        config_menu.addSeparator()

        self.auto_check_updates_action = QAction('Auto-check for Updates', self, checkable=True)
        self.auto_check_updates_action.setStatusTip('Automatically check for updates on startup')
        self.auto_check_updates_action.setChecked(self.auto_check_updates)
        self.auto_check_updates_action.triggered.connect(self.toggle_auto_check_updates)
        config_menu.addAction(self.auto_check_updates_action)

        help_menu.addSeparator()

        users_guide_action = QAction('&Users Guide', self)
        users_guide_action.setStatusTip('Open comprehensive user documentation')
        users_guide_action.triggered.connect(self.show_users_guide)
        help_menu.addAction(users_guide_action)

        help_menu.addSeparator()

        navigation_action = QAction('&Keyboard Shortcuts', self)
        navigation_action.setStatusTip('View available keyboard shortcuts and navigation')
        navigation_action.triggered.connect(self.show_keyboard_shortcuts)
        help_menu.addAction(navigation_action)

        help_menu.addSeparator()

        issue_tracker_action = QAction('&Issue Tracker', self)
        issue_tracker_action.setStatusTip('Report issues or suggest features on GitHub')
        issue_tracker_action.triggered.connect(self.show_issue_tracker)
        help_menu.addAction(issue_tracker_action)

        about_action = QAction('&About', self)
        about_action.setStatusTip('About SysMon')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
