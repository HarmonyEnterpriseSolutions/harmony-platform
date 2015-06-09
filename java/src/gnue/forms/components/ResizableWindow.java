package gnue.forms.components;

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import javax.swing.border.*;
import javax.swing.event.*;

public class ResizableWindow extends JWindow {

	public ResizableWindow(Frame owner) {
		super(owner);
		initUI();
	}

	public ResizableWindow(Window owner) {
		super(owner);
		initUI();
	}

	private void initUI() {
		//setUndecorated(true);

		/* Set a nice border - try to use the internal frame border
		* (used inside JDesktopPane) which should mimic the native
		* frame border when using the system look and feel. */
		//Border border = UIManager.getBorder("InternalFrame.border");
		int w = Math.max(UIManager.getInt("InternalFrame.borderWidth"), 3) - 2;
		Border border = BorderFactory.createCompoundBorder(
			BorderFactory.createBevelBorder(BevelBorder.RAISED),
			BorderFactory.createEmptyBorder(w, w, w, w)
		);

		getRootPane().setBorder(border);

		/* Register the resize listener. */
		ResizeListener resizeListener = new ResizeListener();
		addMouseListener(resizeListener);
		addMouseMotionListener(resizeListener);
	}

	private class ResizeListener extends MouseInputAdapter {

		private static final short RESIZE_E = 1;
		private static final short RESIZE_W = 2;
		private static final short RESIZE_N = 4;
		private static final short RESIZE_S = 8;

		int resizeDirection = 0;

		private Rectangle tempBounds = new Rectangle();

		public void mousePressed(MouseEvent evt) {
			resizeDirection = getResizeDirection(evt);
			if (resizeDirection != 0) {
				setIgnoreRepaint(true);
			}
		}

		public void mouseReleased(MouseEvent evt) {
			resizeDirection = 0;
			setIgnoreRepaint(false);
			validate();
			repaint();
		}

		private short getResizeDirection(MouseEvent evt) {
			short direction = 0;

			int width = getWidth();
			int height = getHeight();
			Insets insets = getRootPane().getInsets();
			int mouseX = evt.getX();
			int mouseY = evt.getY();

			if (mouseX < insets.left) {
				direction |= RESIZE_W;
			} else if (mouseX > width - insets.right) {
				direction |= RESIZE_E;
			}

			if (mouseY < insets.top) {
				direction |= RESIZE_N;
			} else if (mouseY > height - insets.bottom) {
				direction |= RESIZE_S;
			}

			return direction;
		}

		public void mouseMoved(MouseEvent evt) {
			setCursor(Cursor.getPredefinedCursor(getCursorType(getResizeDirection(evt))));
		}

		public void mouseExited(MouseEvent evt) {
			setCursor(Cursor.getPredefinedCursor(Cursor.DEFAULT_CURSOR));
		}

		private int getCursorType(int direction) {
			switch (direction) {
				case RESIZE_S:
					return Cursor.S_RESIZE_CURSOR;
				case RESIZE_E:
					return Cursor.E_RESIZE_CURSOR;
				case RESIZE_N:
					return Cursor.N_RESIZE_CURSOR;
				case RESIZE_W:
					return Cursor.W_RESIZE_CURSOR;
				case RESIZE_S | RESIZE_E:
					return Cursor.SE_RESIZE_CURSOR;
				case RESIZE_N | RESIZE_W:
					return Cursor.NW_RESIZE_CURSOR;
				case RESIZE_N | RESIZE_E:
					return Cursor.NE_RESIZE_CURSOR;
				case RESIZE_S | RESIZE_W:
					return Cursor.SW_RESIZE_CURSOR;
				default:
					return Cursor.DEFAULT_CURSOR;
			}
		}

		public void mouseDragged(MouseEvent evt) {

			Rectangle bounds = getBounds(tempBounds);

			Point mouse = evt.getPoint();
			SwingUtilities.convertPointToScreen(mouse,
			ResizableWindow.this);

			if ((resizeDirection & RESIZE_E) != 0) {
				bounds.width = evt.getX();
			} else if ((resizeDirection & RESIZE_W) != 0) {
				bounds.width += bounds.x - mouse.x;
				bounds.x = mouse.x;
			}

			if ((resizeDirection & RESIZE_S) != 0) {
				bounds.height = evt.getY();
			} else if ((resizeDirection & RESIZE_N) != 0) {
				bounds.height += bounds.y - mouse.y;
				bounds.y = mouse.y;
			}

			setBounds(bounds);
			//validate();
			//repaint();
		}

	}

	public static void main(String[] args) {
		//JFrame f = new JFrame();
		//f.setVisible(true);
		ResizableWindow w = new ResizableWindow((Frame)null);
		w.setBounds(109,10,100,100);
		w.setVisible(true);
		w.add(new JButton("Hello World"));
		w.validate();
	}

}
