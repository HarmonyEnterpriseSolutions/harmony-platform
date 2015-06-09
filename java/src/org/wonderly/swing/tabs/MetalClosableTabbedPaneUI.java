package org.wonderly.swing.tabs;

import javax.swing.plaf.metal.MetalTabbedPaneUI;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import org.wonderly.awt.*;
import java.util.logging.*;
import java.util.*;

class MetalClosableTabbedPaneUI extends MetalTabbedPaneUI implements ClosableTabbedPaneUI {
	Logger log = Logger.getLogger( getClass().getName() );
	CloseableTabbedPane mypane;
	ImageIcon ci;
	ImageIcon dci;

	public MetalClosableTabbedPaneUI( CloseableTabbedPane ctp ) {
		mypane = ctp;
	}

	public void setCloseIcons( ImageIcon icon, ImageIcon downIcon ) {
		ci = icon;
		dci = downIcon;
	}

	public class MouseLis extends MouseAdapter implements MouseMotionListener {
		public void mouseReleased(MouseEvent e) {
			closeIdx = -1;
			tabPane.repaint();
		}

		public void mouseClicked(MouseEvent e) {
			if (!tabPane.isEnabled()) {
				log.finer("clicked, not enabled");
				return;
			}
			if( e.getButton() != 1 ) {
				log.finer("clicked, not button 1");
				return;
			}
			int tabIndex = tabForCoordinate(tabPane, e.getX(), e.getY() );
			if( tabIndex == -1 ) {
				log.finer("clicked no valid tab");
				return;
			}
			if( mypane.unclosable.contains( tabIndex ) ) {
				log.finer("clicked, not closable");
				return;
			}
				
			Rectangle r = closeRectFor( tabIndex );
			// Check for mouse being in close box
			if( r.contains( new Point( e.getX(), e.getY() ) ) ) {
				// Send tab closed message
				mypane.closeTab( tabIndex );
			}
		}

		public void mousePressed(MouseEvent e) {
			if (!tabPane.isEnabled()) {
				return;
			}
			if( e.getButton() != 1 ) {
				log.finer("Not button 1");
				return;
			}
			int tabIndex = tabForCoordinate(tabPane, e.getX(), e.getY() );
			if( tabIndex == -1 ) {
				log.finer("No valid tab index");
				return;
			}
			if( mypane.unclosable.contains( tabIndex ) ) {
				log.finer("Non-closable tab");
				return;
			}
			Rectangle r = closeRectFor( tabIndex );
			if( r.contains( new Point( e.getX(), e.getY() ) ) )
				closeIdx = tabIndex;
			else
				closeIdx = -1;
			tabPane.repaint();
		}
	
		public void mouseDragged(MouseEvent e) {
			mouseMoved(e);
			mousePressed(e);
		}
		
		public void mouseMoved(MouseEvent e) {
			if (tabPane == null || !tabPane.isEnabled()) {
				log.finer("Tabpane disabled");
				return;
			}
			int tabIndex = tabForCoordinate(tabPane, e.getX(), e.getY() );
			if( tabIndex == -1 ) {
				log.finer("not on a tab");
				return;
			}
			if( mypane.unclosable.contains( tabIndex ) ) {
				log.finer("non-closable tab");
				return;
			}
			Rectangle r = closeRectFor( tabIndex );
			log.finer( "rects[tabIndex].x = "+rects[tabIndex].x+", "+
				"rects[tabIndex].y="+rects[tabIndex].y+", "+
				"rects[tabIndex].width="+rects[tabIndex].width+", "+
				"closeWidth="+closeWidth+", "+
				"closeWidth/2="+(closeWidth/2)+", "+
				"m.x="+e.getX()+", m.y="+e.getY()+", r="+r );
			if( r.contains( new Point( e.getX(), e.getY() ) ) )
				closeOverIdx = tabIndex;
			else
				closeOverIdx = -1;
			tabPane.repaint();
		}
	}

	private Rectangle closeRectFor( int tabIndex ) {
		int cw = closeWidth();
		return new Rectangle( rects[tabIndex].x+rects[tabIndex].width-cw-cw/2,
			rects[tabIndex].y+(lastTabHeight-
				(ci == null ? cw : ci.getIconHeight()))/2,
			cw, cw+1 );
	}

	/**
		*  Override this to provide extra space on right for close button
		*/
	protected int calculateTabWidth(int tabPlacement, int tabIndex, FontMetrics metrics) {
		int w = super.calculateTabWidth( tabPlacement, tabIndex, metrics );
		if( mypane.unclosable.contains( tabIndex ) == false )
			w += closeWidth() + closeWidth()/2;
		return w;
	}

	volatile int lastTabHeight = 0;
	/**
		*  Override this to provide extra space on right for close button
		*/
	protected int calculateTabHeight(int tabPlacement, int tabIndex, int v ) {
		int h = super.calculateTabHeight( tabPlacement, tabIndex, v );
		if( mypane.unclosable.contains( tabIndex ) == false )
			h = Math.max( h, (ci != null ? ci.getIconHeight() : closeWidth) + 6 );
		return lastTabHeight = h;
	}
		
	public int closeWidth() {
		return ci != null ? ci.getIconWidth() : closeWidth;
	}

	volatile int closeIdx = -1;
	volatile int closeWidth = 14;
	volatile int closeOverIdx = -1;

	int closeDownIdx() {
		return closeIdx;
	}

	protected void paintText(Graphics g, int tabPlacement,
							Font font, FontMetrics metrics, int tabIndex,
							String title, Rectangle textRect, 
							boolean isSelected) {
		Rectangle r = new Rectangle( textRect );
		if( mypane.unclosable.contains( tabIndex ) == false ) {
			r.x -= closeWidth - (closeWidth/2);
		}
		super.paintText( g, tabPlacement, font, metrics, tabIndex,
			title, r, isSelected );
	}

	protected void paintIcon(Graphics g, int tabPlacement,
								int tabIndex, Icon icon, Rectangle iconRect, 
								boolean isSelected ) {
		Rectangle r = new Rectangle( iconRect );
		if( mypane.unclosable.contains( tabIndex ) == false ) {
			r.x -= closeWidth - (closeWidth/2);
		}
		super.paintIcon( g, tabPlacement, tabIndex, icon, r, isSelected );
	}

	protected void paintTabBackground(Graphics g, int tabPlacement,
										int tabIndex,
										int x, int y, int w, int h, 
										boolean isSelected ) {
		super.paintTabBackground( g, tabPlacement, tabIndex, x, y, w, h, isSelected );
		if( mypane.unclosable.contains( tabIndex ) )
			return;
		final int ov = closeWidth();
		if( ci != null ) {
			g.drawImage( closeDownIdx() != tabIndex ?
				ci.getImage() : dci.getImage(), x+w-ov-(ov/2), y+(h-ci.getIconHeight())/2+1, mypane );
		} else {
			// Get a constant, immutable value for painting.
			g.setColor( ( closeOverIdx == tabIndex && closeDownIdx() == -1 ) ? 
				new Color( 220, 230, 255 ) : Color.gray.brighter() );
			g.fill3DRect( x+w-ov-(ov/2), y+(h-ov)/2, ov, ov, closeDownIdx() != tabIndex );
			g.draw3DRect( x+w-ov-(ov/2)-1, y+(h-ov)/2, ov+1, ov+1, closeDownIdx() != tabIndex );
			g.setColor(Color.black);
			g.drawLine( x+w-(ov/2)-0, y+((h-ov)/2)+0, x+w-ov-(ov/2)+2, y+((h-ov)/2)+ov-2);
			g.drawLine( x+w-ov-(ov/2)+2, y+((h-ov)/2)+2, x+w-(ov/2)-2, y+((h-ov)/2)+ov-2);
		}
	}
		
	protected void installListeners() {
		super.installListeners();
		MouseLis mlis = new MouseLis();
		tabPane.addMouseListener( mlis );
		tabPane.addMouseMotionListener( mlis );
	}
	
	public void setCloseWidth( int width ) {
		this.closeWidth = width;
	}
	
}
