package gnue.forms.ui;

import javax.swing.*;
import javax.swing.table.*;
import javax.swing.event.*;
import java.awt.AWTEvent;
import java.awt.Component;
import java.awt.EventQueue;
import java.awt.Toolkit;
import java.awt.Rectangle;
import java.awt.event.*;
import java.awt.datatransfer.*;
import org.json.*;
import java.util.List;
import java.util.ArrayList;
import java.util.Iterator;
import gnue.forms.components.*;
import gnue.forms.components.table.*;
import gnue.forms.components.PopupControl;

public class Table extends Widget implements ListSelectionListener, MouseListener, KeyListener {

	private JTable table;
	private boolean stateSet;
	List<Entry> entries = new ArrayList<Entry>();
	boolean selectionChange = false;
	JPopupMenu popupMenu = null;
	static final int baseFlagsCol = 1;
	int baseDataCol;
	TableCellRenderer rowHeaderRenderer = null;

	public Table(Desktop desktop, Integer id, String label, String selectionMode) {
		super(desktop, id, label);

		table = new TableComponent(new TableDoc());

		table.addMouseListener(this);
		table.addKeyListener(this);

		table.getTableHeader().addMouseMotionListener(new ColumnHeaderToolTipsListener());
		table.getTableHeader().addMouseListener(new TableColumnFitData());
		table.getTableHeader().addMouseListener(new ColumnHeaderSelectionListener());
		
		table.setRowSelectionAllowed("rows".equals(selectionMode) || "cells".equals(selectionMode));
		table.setColumnSelectionAllowed("columns".equals(selectionMode) || "cells".equals(selectionMode));
		
		// table gains focus but it is not WidgetNavigable 
		// so after table, OnSetFocus may be skipped because lastFocusOwner not changed to table - #197
		table.addFocusListener(new FocusAdapter() {
			public void focusGained(FocusEvent event) {
				// avoid onSetFocus if focus was requested
				if (getId().equals(getDesktop().lastRequestFocusWidgetId)) {
					getDesktop().lastRequestFocusWidgetId = null;
				}
				else {
					// avoid subsequent onSetFocus when browser window activated
					if (event.getSource() != WidgetNavigable.lastFocusOwner) {
						WidgetNavigable.lastFocusOwner = event.getSource();
					} 
				}
			}
		});
		
		//table.setCellSelectionEnabled(true); //"cells".equals(selectionMode));
		JScrollPane scrollPane = new JScrollPane(table);

		setComponent(scrollPane);
		
	}
	
	public void uiSetPopupMenu(Widget widget) {
		this.popupMenu = (JPopupMenu)widget.getComponent();
	}

	public void valueChanged(ListSelectionEvent e) {
		// The mouse button has not yet been released
		if (!e.getValueIsAdjusting()) {
			call(
				"onSelectionChange",
				table.getSelectedRow(),
				Math.max(0, table.getSelectedColumn() - baseDataCol),
				table.getSelectedRows()
			);
			/*if (!selectionChange) {
				selectionChange = true;
				SwingUtilities.invokeLater(new Runnable(){
					public void run() {
						call("onSelectionChange", table.getSelectedRow(), table.getSelectedColumn(), table.getSelectedRows());

						// this flag intended to awoid duplicate calls
						selectionChange = false;
					}
				});
			}*/
		}
	}

	public void uiSetColumns(JSONArray flags, JSONArray columns) {
		getModel().setColumns(flags, columns);

		// add line number column renderer
		if (rowHeaderRenderer == null) {
			rowHeaderRenderer = createDefaultRowHeaderRenderer();
		}
		table.getColumnModel().getColumn(0).setCellRenderer(rowHeaderRenderer);

		baseDataCol = baseFlagsCol + flags.length();

		// set flag editors
		for (int i=baseFlagsCol; i<baseDataCol; i++) {
			TableColumn column = table.getColumnModel().getColumn(i);
			column.setCellEditor(new DefaultCellEditor(new JCheckBox()));
			int w = table.getRowHeight();
			column.setPreferredWidth(w);
			column.setMinWidth(w);
			column.setMaxWidth(w);
		}

		// set data editors
		for (int i=0; i<entries.size(); i++) {
			table.getColumnModel().getColumn(baseDataCol+i).setCellEditor(new TableEditor(this, entries.get(i)));
		}
		
		// set column identifiers
		for (int i=baseDataCol; i<columns.length(); i++) {
			table.getColumnModel().getColumn(i).setIdentifier(columns.getJSONObject(i).getString("id"));
		}
		
	}
	
	protected TableCellRenderer createDefaultRowHeaderRenderer() {
		DefaultTableCellRenderer renderer = new DefaultTableCellRenderer() {
			public Component getTableCellRendererComponent(JTable table, Object value, boolean flag, boolean flag1, int row, int col) {
				boolean currentRow = table.isRowSelected(row);
				JTableHeader tableHeader = table.getTableHeader();
				setForeground(currentRow ? table.getSelectionForeground() : tableHeader.getForeground());
				setBackground(currentRow ? table.getSelectionBackground() : tableHeader.getBackground());
				setFont(tableHeader.getFont());
				// how to add right margin?
				setText(value.toString());
				setBorder(UIManager.getBorder("TableHeader.cellBorder"));
				return this;
			}
		};
		renderer.setHorizontalAlignment(SwingConstants.CENTER);
		return renderer;
	}
	
	
	/**
	 * data is JSONArray of JSONArrays of String or Boolean for flag data
	 * columns is JSONArray of JSONObject similar to uiSetColumns, used to update columns
	 */
	public void uiSetData(JSONArray data, JSONArray columns) {
		stopListenSelection();
		try {
			getModel().setData(data, columns);
		}
		finally {
			startListenSelection();
		}
		
		TableColumnModel cm = table.getColumnModel();

		//update column names for sort marks
		for (int col = 0; col < cm.getColumnCount(); col++) {
			cm.getColumn(col).setHeaderValue(getModel().getColumnName(col));
		}
		
		// set column optimal sizes
		if (!stateSet) {
			for (int col = baseDataCol; col < cm.getColumnCount(); col++) {
				//if (!state.has((String)cm.getColumn(col).getIdentifier())) {
				TableColumnFitData.updateColumnPreferredWidth(table, col, false);
				//}
			}
			stateSet = true;
		}

		// set row number column optimal sizes
		TableColumnFitData.updateColumnPreferredWidth(table, 0, true, 0);
		TableColumn numberColumn = cm.getColumn(0);
		numberColumn.setMinWidth(numberColumn.getPreferredWidth());
		numberColumn.setMaxWidth(numberColumn.getPreferredWidth());
	}

	protected void stopListenSelection() {
		table.getSelectionModel().removeListSelectionListener(this);
		table.getColumnModel().getSelectionModel().removeListSelectionListener(this);
	}
	
	protected void startListenSelection() {
		table.getSelectionModel().addListSelectionListener(this);
		table.getColumnModel().getSelectionModel().addListSelectionListener(this);
	}
	

	public void uiSetRowData(Integer row, JSONArray rowData) {
		getModel().setRowData(row, rowData);
	}

	public void uiAdd(Widget widget) {
		entries.add((Entry)widget);
		getModel().addColumnClass(((Entry)widget).getColumnClass());
	}

	public void uiSetFocusedRow(Integer row) {
		setFocusedCell(row, table.getSelectedColumn()-baseDataCol);
	}

	public void uiSetFocusedCell(Integer row, Integer col) {
		if (!table.isFocusOwner()) {
			// request focus if it is applet child
			java.awt.Container c = table.getParent();
			while (c != null ) {
				if (c instanceof java.applet.Applet) {
					table.requestFocus();
					break;
				}
				// request focus if it is not applet child but top level window is already focused
				if (c instanceof java.awt.Window) {
					if (((java.awt.Window)c).isFocused()) {
						table.requestFocus();
						break;
					}
				}
				c = c.getParent();
			}
		}
		setFocusedCell(row, col);
	}

	private void setFocusedCell(Integer row, Integer col) {
		table.getSelectionModel().removeListSelectionListener(this);
		table.getColumnModel().getSelectionModel().removeListSelectionListener(this);
		try {
			table.changeSelection(row, col+baseDataCol, false, false);
		}
		finally {
			table.getSelectionModel().addListSelectionListener(this);
			table.getColumnModel().getSelectionModel().addListSelectionListener(this);
		}
	}

	public void uiCancelEditing() {
		if (table.isEditing()) {
			table.getCellEditor().cancelCellEditing();
		}
	}

	public void uiStopEditing() {
		if (table.isEditing()) {
			table.getCellEditor().stopCellEditing();
		}
	}
	
	protected Rectangle getSelectedBlock() {
		Rectangle block = new Rectangle();
		int[] rows = table.getSelectedRows();
		int[] cols = table.getSelectedColumns();
		
		// remove flags and label from selected columns
		List<Integer> dataCols = new ArrayList<Integer>();
		for (int col: cols) {
			if (col > baseDataCol) {
				dataCols.add(col);
			}
		}
		cols = new int[dataCols.size()];
		for (int i=0; i<dataCols.size(); i++) {
			cols[i] = dataCols.get(i);
		}
		
		if (rows.length > 0 && cols.length > 0) {
			int minRow = rows[0];
			int minCol = cols[0];
			int maxRow = minRow;
			int maxCol = minCol;
			for (int row: rows) {
				minRow = Math.min(minRow, row);
				maxRow = Math.max(maxRow, row);
			}
			for (int col: cols) {
				minCol = Math.min(minCol, col);
				maxCol = Math.max(maxCol, col);
			}
			block.x = minCol;
			block.y = minRow;
			block.width = maxCol - minCol + 1;
			block.height = maxRow - minRow + 1;
		}
		return block;
	}
	
	public void uiCut() {
		Rectangle block = getSelectedBlock();
		if (!block.isEmpty()) {
			uiCopy();
			call("onErase", block.y, block.x-baseFlagsCol, block.height, block.width);
		}
	}
	
	public void uiCopy() {
		Rectangle block = getSelectedBlock();
		/*StringBuffer text = new StringBuffer();
		for (int i=0; i<block.height; i++) {
			if (i > 0) text.append("\n");
			for (int j=0; j<block.width; j++) {
				if (j > 0) text.append("\t");
				text.append(getModel().getValueAt(block.y + i, block.x + j));
			}
		};*/
		System.out.println(">>> Selected block: " + block);
		String text = (String)call("onCopy", block.y, block.x-baseFlagsCol, block.height, block.width);
		StringSelection data = new StringSelection(text);
		Toolkit.getDefaultToolkit().getSystemClipboard().setContents(data, data);
	}

	public void uiPaste() {
		Transferable data = Toolkit.getDefaultToolkit().getSystemClipboard().getContents(null);
		if (data != null) {
			try {
	           	callAfter("onPaste", (String)data.getTransferData(DataFlavor.stringFlavor));
			}
			catch(UnsupportedFlavorException e) {}
			catch(java.io.IOException e) {} // never thrown
		}
	}

	public TableDoc getModel() {
		return (TableDoc)table.getModel();
	}

	public boolean isVerticalGrowable() {
		return true;
	}
	
	public int getHorizontalAlignment(int col) {
		switch ((entries.get(col-baseDataCol).getAlign() - 1) % 3) {
			case 0: return SwingConstants.LEFT;
			case 1: return SwingConstants.CENTER;
			case 2: return SwingConstants.RIGHT;
			default:
				throw new RuntimeException();	// unreachable
		}
	}

	public int getVerticalAlignment(int col) {
		int align = entries.get(col-baseDataCol).getAlign();
		switch ((align - 1) / 3) {
			case 0: return SwingConstants.BOTTOM;
			case 1: return SwingConstants.CENTER;
			case 2: return SwingConstants.TOP;
			default:
				throw new RuntimeException("Align must be 1..9, got " + align);
		}
	}	

	//////////////////////////////////////////////////////////////////////////////////////////////////
	// customized JTable
	//

	class TableComponent extends JTable {

		//private final int COLUMN_EXTRA_WIDTH = 4;
		
		public TableComponent(TableModel model) {
			super(model);
			
			// force editor to have focus (and cursor) on keystroke
			setSurrendersFocusOnKeystroke(true);

			/*TableCellRenderer renderer = getTableHeader().getDefaultRenderer();

			for (int i = 0; i < getColumnCount(); ++i) {
				 getColumnModel().getColumn(i).setPreferredWidth(
					renderer.getTableCellRendererComponent(
						this,
						getModel().getColumnName(i),
						false, false, 0, i
					).getPreferredSize().width
				 );
			}*/
			
			getSelectionModel().addListSelectionListener(this);
			getColumnModel().getSelectionModel().addListSelectionListener(this);
			setAutoResizeMode(JTable.AUTO_RESIZE_OFF);
			getTableHeader().setReorderingAllowed(false);
			setRowHeight(new JTextField().getPreferredSize().height);
			
			setSelectionMode(ListSelectionModel.MULTIPLE_INTERVAL_SELECTION);
		
			// Handle escape key on a JTable
			
			/*
			Action escapeAction = new AbstractAction() {
				public void actionPerformed(ActionEvent e) {
					if (TableComponent.this.isEditing()) {
						int row = TableComponent.this.getEditingRow();
						int col = TableComponent.this.getEditingColumn();
						TableComponent.this.getCellEditor(row, col).cancelCellEditing();
					}
				}
			};
			KeyStroke escape = KeyStroke.getKeyStroke(KeyEvent.VK_ESCAPE, 0, false);
			this.getInputMap(JTable.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(escape, "ESCAPE");
			this.getActionMap().put("ESCAPE", escapeAction);
			*/
			
		}

		/**
		 * disable DOWN hotkey in editor with popup control 
		 * disable TAB end ENTER hotkeys in editor
		 */
		protected boolean processKeyBinding(KeyStroke stroke, KeyEvent evt, int condition, boolean pressed) {
			Component editorComponent = this.getEditorComponent();
			if (editorComponent != null) {
				// suppress DOWN behaviour for PopupControl editors
				if (editorComponent instanceof PopupControl) {
					if (evt.getKeyCode() == KeyEvent.VK_DOWN) {
				    	return false;
					}
				}
				// if ESC pressed in editor, cancelCellEditing and suppres JTable behaviour
				if (evt.getKeyCode() == KeyEvent.VK_ESCAPE && !stroke.isOnKeyRelease()) {
					int row = this.getEditingRow();
					int col = this.getEditingColumn();
					this.getCellEditor(row, col).cancelCellEditing();
					return false;
				}
				// this will be handled thrue gnue server
				//if (
				//	   evt.getKeyCode() == KeyEvent.VK_TAB 
				//	|| evt.getKeyCode() == KeyEvent.VK_ENTER 
				//) {
				//	return false;
				//}
			}
			return super.processKeyBinding(stroke, evt, condition, pressed);
		}

		/**
		 * disable navigation with TAB and ENTER
		 * navigation will be done via gnue logic
		 */
		public void changeSelection(int rowIndex, int columnIndex, boolean toggle, boolean extend) {
			AWTEvent currentEvent = EventQueue.getCurrentEvent();
			if (currentEvent != null &&  currentEvent instanceof KeyEvent) {
				// && currentEvent.getSource() == this
				final KeyEvent event = (KeyEvent)currentEvent;
				KeyStroke ks = KeyStroke.getKeyStrokeForEvent(event);
				// disable tab and enter
				if (   ks.equals(KeyStroke.getKeyStroke(KeyEvent.VK_TAB,   0))
					|| ks.equals(KeyStroke.getKeyStroke(KeyEvent.VK_TAB,   InputEvent.SHIFT_MASK))
					|| ks.equals(KeyStroke.getKeyStroke(KeyEvent.VK_ENTER, 0))
					|| ks.equals(KeyStroke.getKeyStroke(KeyEvent.VK_ENTER, InputEvent.SHIFT_MASK))
				) {
					return;
				}
			}
			super.changeSelection(rowIndex, columnIndex, toggle, extend);
		}

		public Component prepareRenderer(final TableCellRenderer renderer, final int row, final int column) {
			final Component prepareRenderer = super.prepareRenderer(renderer, row, column);

			if (renderer instanceof JLabel) {
				JLabel label = (JLabel)renderer;

				// set align
				if (column >= baseDataCol) {
					label.setHorizontalAlignment(getHorizontalAlignment(column));
					label.setVerticalAlignment(getVerticalAlignment(column));
				}
				else {
					// not reachable?
					label.setHorizontalAlignment(SwingConstants.CENTER);
					label.setVerticalAlignment(SwingConstants.CENTER);
				}
			}
			return prepareRenderer;
		}

		//public Component prepareEditor(TableCellEditor tableCellEditor, int i, int j) {
		//	Component c = super.prepareEditor(tableCellEditor, i, j);
		//	if (tableCellEditor instanceof TableEditor) {
		//		((TableEditor)tableCellEditor).improveFocus();
		//	}
		//    return c;
		//}
	

	}

	//////////////////////////////////////////////////////////////////////////////////////////////////
	// mouse listener
	//

	public void mouseClicked(MouseEvent event) {
		if (event.getButton() == event.BUTTON1 && event.getClickCount() == 2) {
			callAfter("onRowActivated");
		}
	}
	public void mousePressed(MouseEvent event) {
		if (event.getButton() == MouseEvent.BUTTON3) {
			int row = table.rowAtPoint(event.getPoint());
			int col = table.columnAtPoint(event.getPoint());
			if (row >= 0 && col > 0 && !table.isCellSelected(row, col)) {
				table.changeSelection(row, col, false, false);
			}
		}
		mouseMaybePopup(event);
	}
	public void mouseReleased(MouseEvent event) {
		mouseMaybePopup(event);
	}
	private void mouseMaybePopup(MouseEvent event) {
		if (event.isPopupTrigger()) {
			if (popupMenu != null) {
				call("onMenuPopup", table.getSelectedRows(), table.getSelectedColumn()-baseFlagsCol);
				popupMenu.show((JComponent)event.getSource(), event.getX(), event.getY());
			}
		}
	}
	public void mouseEntered(MouseEvent event) {}
	public void mouseExited(MouseEvent event) {}

	//////////////////////////////////////////////////////////////////////////////////////////////////
	// key listener
	//

	public void keyPressed(final KeyEvent event) {
		SwingUtilities.invokeLater(new Runnable() {
			public void run() {
				switch (event.getKeyCode()) {
					case KeyEvent.VK_ENTER:
						if (table.getSelectedRow() >= 0 && table.getSelectedColumn() >= 0 && !table.isCellEditable(table.getSelectedRow(), table.getSelectedColumn())) {
							appendCall("onRowActivated");
							break;
						}
						// no break, proceed
					case KeyEvent.VK_TAB:
						appendCall("onKeyPressed", event.getKeyCode(), event.isShiftDown(), event.isControlDown(), event.isAltDown());
						break;
				}
				flushIfPending();
			}
		});
	}
	public void keyReleased(final KeyEvent event) {}
	public void keyTyped(final KeyEvent event) {}

	//////////////////////////////////////////////////////////////////////////////////////////////////
	// tips
	//

	class ColumnHeaderToolTipsListener extends MouseMotionAdapter {
		// Current column whose tooltip is being displayed.
		// This variable is used to minimize the calls to setToolTipText().
		private int prevColIndex = -1;

		public void mouseMoved(MouseEvent evt) {
			JTableHeader header = (JTableHeader)evt.getSource();
			JTable table = header.getTable();
			int colIndex = table.getColumnModel().getColumnIndexAtX(evt.getX());

			// Return if not clicked on any column header
			if (colIndex >= 0 && colIndex != prevColIndex) {
				String tip = getModel().getColumnTip(colIndex);
				header.setToolTipText(tip.length() > 0 ? tip : null);
				prevColIndex = colIndex;
			}

		}
	}

	class ColumnHeaderSelectionListener extends MouseAdapter {
		public void mouseClicked(MouseEvent evt) {
			int colIndex = table.getColumnModel().getColumnIndexAtX(evt.getX());
			if (colIndex == 0) {
				stopListenSelection();
				try {
					table.selectAll();
				}
				finally {
					startListenSelection();
				}
			}
		}
	}

	//////////////////////////////////////////////////////////////////////////////
	// state
	//
	public JSONObject getState() {
		JSONObject state = new JSONObject();

		TableColumnModel cm = table.getColumnModel();

		for (int col = baseDataCol; col < cm.getColumnCount(); col++) {
			TableColumn column = cm.getColumn(col);
			String id = (String)column.getIdentifier();
			state.put((String)column.getIdentifier(), column.getWidth());
			
		}

		return state;
	}

	public void setState(JSONObject state) {

		for (Iterator ids = state.keys(); ids.hasNext();) {
			String id = (String)ids.next();
			try {
				table.getColumn(id).setPreferredWidth(state.getInt(id));
				//stem.out.println("+ Set column "+id+" width: " + state.getInt(id));
			}
			catch (IllegalArgumentException e) {
				// no such column (removed in gfd)
				//stem.out.println("! No such column: " + id);
			}
		}

		// if state was not set columns are autosized in uiSetData
		stateSet = true;
	}

}
